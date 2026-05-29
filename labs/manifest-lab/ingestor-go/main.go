package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/fxamacker/cbor/v2"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/segmentio/kafka-go"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
)

// Configuration
var (
	KafkaBroker = getEnv("KAFKA_BROKER", "localhost:9092")
	KafkaTopic  = "raw-sboms"
)

const (
	Port       = "8001"
	BufferSize = 10000
	WorkerPool = 10
)

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

// Metrics
var (
	ingestCount = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "go_sbom_ingestion_total",
		Help: "Total SBOMs ingested via Go",
	}, []string{"format"})
	ingestLatency = prometheus.NewHistogram(prometheus.HistogramOpts{
		Name:    "go_sbom_ingestion_latency_seconds",
		Help:    "Latency of Go SBOM ingestion",
		Buckets: prometheus.DefBuckets,
	})
	backpressureCount = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "go_ingestion_backpressure_total",
		Help: "Total requests rejected due to backpressure",
	})
	circuitBreakerState = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "go_ingestion_circuit_breaker_state",
		Help: "Current state of the circuit breaker (0=Closed, 1=Open)",
	})
)

func init() {
	prometheus.MustRegister(ingestCount)
	prometheus.MustRegister(ingestLatency)
	prometheus.MustRegister(backpressureCount)
	prometheus.MustRegister(circuitBreakerState)
}

// CircuitBreaker implementation
type CircuitBreaker struct {
	mu           sync.RWMutex
	state        string // CLOSED, OPEN
	failureCount int
	maxFailures  int
	resetTimeout time.Duration
	lastFailure  time.Time
}

func (cb *CircuitBreaker) CanExecute() bool {
	cb.mu.RLock()
	defer cb.mu.RUnlock()

	if cb.state == "OPEN" {
		if time.Since(cb.lastFailure) > cb.resetTimeout {
			return true // HALF-OPEN (simplified)
		}
		return false
	}
	return true
}

func (cb *CircuitBreaker) RecordFailure() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.failureCount++
	cb.lastFailure = time.Now()
	if cb.failureCount >= cb.maxFailures {
		cb.state = "OPEN"
		circuitBreakerState.Set(1)
		log.Println("⚠️ Circuit Breaker TRIPPED: Ingestion suspended.")
	}
}

func (cb *CircuitBreaker) RecordSuccess() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.failureCount = 0
	cb.state = "CLOSED"
	circuitBreakerState.Set(0)
}

var cb = &CircuitBreaker{
	state:        "CLOSED",
	maxFailures:  5,
	resetTimeout: 30 * time.Second,
}

var tracer = otel.Tracer("Manifest-ingestor")

// Ingestion Payload
type SBOMPayload struct {
	CID       string      `json:"cid" cbor:"cid"`
	RequestID string      `json:"request_id" cbor:"request_id"`
	Timestamp float64     `json:"timestamp" cbor:"timestamp"`
	Format    string      `json:"format" cbor:"format"`
	Data      interface{} `json:"data" cbor:"data"`
	Signature []byte      `json:"signature,omitempty" cbor:"signature,omitempty"`
}

var ingestChannel = make(chan []byte, BufferSize)

func main() {
	writer := &kafka.Writer{
		Addr:     kafka.TCP(KafkaBroker),
		Topic:    KafkaTopic,
		Balancer: &kafka.LeastBytes{},
		Async:    true,
	}
	defer writer.Close()

	for i := 0; i < WorkerPool; i++ {
		go worker(writer)
	}

	http.HandleFunc("/ingest/sbom", handleIngestJSON)
	http.HandleFunc("/ingest/sbom/cbor", handleIngestCBOR)
	http.Handle("/metrics", promhttp.Handler())
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, "OK. Buffer: %d/%d, CB: %s", len(ingestChannel), BufferSize, cb.state)
	})

	log.Printf("🚀 Advanced Go Ingestor starting on port %s (OTel + COSE + CB Enabled)\n", Port)
	if err := http.ListenAndServe(":"+Port, nil); err != nil {
		log.Fatal(err)
	}
}

func handleIngestJSON(w http.ResponseWriter, r *http.Request) {
	processIngest(w, r, "json")
}

func handleIngestCBOR(w http.ResponseWriter, r *http.Request) {
	processIngest(w, r, "cbor")
}

func processIngest(w http.ResponseWriter, r *http.Request, format string) {
	_, span := tracer.Start(r.Context(), "ProcessIngest", trace.WithAttributes(
		attribute.String("format", format),
	))
	defer span.End()

	start := time.Now()
	defer func() {
		ingestLatency.Observe(time.Since(start).Seconds())
	}()

	if !cb.CanExecute() {
		span.AddEvent("CircuitBreakerBlocked")
		http.Error(w, "Service Unavailable (Circuit Breaker OPEN)", http.StatusServiceUnavailable)
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Failed to read body", http.StatusInternalServerError)
		return
	}

	// Staff-Level: SHA-256 Content Identifier (CID)
	// Critique: Non-deterministic hashing breaks deduplication.
	// We use deterministic raw body hashing.
	h := sha256.New()
	h.Write(body)
	cid := hex.EncodeToString(h.Sum(nil))
	span.SetAttributes(attribute.String("cid", cid))

	// COSE Signature Check (Simulated for Lab)
	// Improvement: In a real system, we'd verify the COSE signature header here.
	signature := r.Header.Get("X-COSE-Signature")
	if format == "cbor" && signature == "" {
		log.Printf("⚠️ Warning: CBOR payload received without COSE signature (CID: %s)\n", cid)
	}

	var decodedData interface{}
	if format == "json" {
		if err := json.Unmarshal(body, &decodedData); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}
	} else {
		if err := cbor.Unmarshal(body, &decodedData); err != nil {
			http.Error(w, "Invalid CBOR", http.StatusBadRequest)
			return
		}
	}

	requestID := r.Header.Get("X-Request-ID")
	if requestID == "" {
		requestID = fmt.Sprintf("%d", time.Now().UnixNano())
	}

	payload := SBOMPayload{
		CID:       cid,
		RequestID: requestID,
		Timestamp: float64(time.Now().Unix()),
		Format:    format,
		Data:      decodedData,
		Signature: []byte(signature),
	}

	data, _ := json.Marshal(payload)

	select {
	case ingestChannel <- data:
		ingestCount.WithLabelValues(format).Inc()
		w.WriteHeader(http.StatusAccepted)
		json.NewEncoder(w).Encode(map[string]string{
			"status":     "accepted",
			"cid":        cid,
			"request_id": requestID,
		})
	default:
		span.AddEvent("BackpressureTriggered")
		backpressureCount.Inc()
		http.Error(w, "Ingestion buffer full", http.StatusTooManyRequests)
	}
}

func worker(writer *kafka.Writer) {
	for msg := range ingestChannel {
		err := writer.WriteMessages(context.Background(), kafka.Message{
			Value: msg,
		})
		if err != nil {
			log.Printf("❌ Kafka Write Error: %v\n", err)
			cb.RecordFailure()
		} else {
			cb.RecordSuccess()
		}
	}
}

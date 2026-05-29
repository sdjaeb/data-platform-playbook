package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"sync"
	"sync/atomic"
	"time"
)

func main() {
	targetURL := flag.String("url", "http://localhost:8001/ingest/sbom", "Target URL")
	concurrency := flag.Int("c", 5000, "Number of concurrent workers")
	duration := flag.Int("d", 10, "Duration of test in seconds")
	targetRate := flag.Int("rate", 150000, "Target TPS")
	flag.Parse()

	payload, _ := json.Marshal([]map[string]string{
		{"name": "stress-component", "version": "1.0.0"},
	})

	var accepted int64
	var rejected int64
	var failed int64
	var budget int64 // Shared budget for the current millisecond

	// Highly optimized transport for Darwin/Linux socket pressure
	client := &http.Client{
		Transport: &http.Transport{
			MaxIdleConns:        20000,
			MaxIdleConnsPerHost: 20000,
			IdleConnTimeout:     90 * time.Second,
			DisableCompression:  true,
			DisableKeepAlives:   false,
		},
		Timeout: 2 * time.Second,
	}

	fmt.Printf("🚀 Starting Manifest STAFF-SCALE Stress Test...\n")
	fmt.Printf("Target: %s | Goal: %d TPS\n", *targetURL, *targetRate)

	start := time.Now()
	done := make(chan bool)
	var wg sync.WaitGroup

	// Staff Logic: The Budget Refiller
	// We refill the budget 1000 times per second to hit the target rate
	go func() {
		ticker := time.NewTicker(time.Millisecond)
		perTick := int64(*targetRate / 1000)
		for {
			select {
			case <-done:
				return
			case <-ticker.C:
				atomic.Store64(&budget, uint64(perTick))
			}
		}
	}()

	// Worker Pool
	for i := 0; i < *concurrency; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-done:
					return
				default:
					// Try to grab budget
					currentBudget := atomic.Load64(&budget)
					if currentBudget > 0 {
						if atomic.CompareAndSwap64(&budget, currentBudget, currentBudget-1) {
							// Execute Request
							resp, err := client.Post(*targetURL, "application/json", bytes.NewBuffer(payload))
							if err != nil {
								atomic.AddInt64(&failed, 1)
								continue
							}
							
							if resp.StatusCode == http.StatusAccepted {
								atomic.AddInt64(&accepted, 1)
							} else if resp.StatusCode == http.StatusTooManyRequests {
								atomic.AddInt64(&rejected, 1)
							} else {
								atomic.AddInt64(&failed, 1)
							}
							resp.Body.Close()
						}
					} else {
						// Small sleep to prevent CPU spin-lock if budget is empty
						time.Sleep(100 * time.Microsecond)
					}
				}
			}
		}()
	}

	time.Sleep(time.Duration(*duration) * time.Second)
	close(done)
	wg.Wait()
	
	elapsed := time.Since(start).Seconds()
	total := accepted + rejected + failed
	tps := float64(total) / elapsed

	fmt.Printf("\n--- Stress Test Results ---\n")
	fmt.Printf("Actual TPS:     %.2f req/sec\n", tps)
	fmt.Printf("✅ Accepted:    %d\n", accepted)
	fmt.Printf("⚠️  Rejected:    %d (Backpressure!)\n", rejected)
	fmt.Printf("❌ Failed:      %d (OS Socket Limits)\n", failed)
}

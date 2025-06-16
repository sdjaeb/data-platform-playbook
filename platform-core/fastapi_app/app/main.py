# fastapi_app/app/main.py
# This script defines a FastAPI application that serves as a data ingestor.
# It receives financial transactions and insurance claims via HTTP POST requests,
# publishes them to Apache Kafka topics, and is instrumented with OpenTelemetry
# to emit metrics, logs, and traces for observability.

import os
import json
import time # For simulating processing time for histogram
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from kafka import KafkaProducer

# --- OpenTelemetry Imports and Setup ---
# OpenTelemetry API for defining telemetry data
from opentelemetry import metrics, trace
# OpenTelemetry SDK for configuring how telemetry data is processed and exported
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
# OTLP (OpenTelemetry Protocol) exporters for sending data over HTTP
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
# Auto-instrumentation for FastAPI and Python's logging
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Resource defines attributes about the service, useful for filtering and identifying
# telemetry data in monitoring systems (e.g., Grafana, Jaeger).
resource = Resource.create({
    "service.name": "fastapi-ingestor",
    "service.version": "1.0.0",
    "env.type": "local-dev"
})

# Configure OTLP Exporter endpoint (Grafana Alloy).
# This environment variable should be set in docker-compose.yml for the fastapi_ingestor service.
# It points to Grafana Alloy's OTLP HTTP receiver.
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://grafana_alloy:4318")

# --- Metrics Setup ---
# OTLPMetricExporter sends metrics to the configured OTLP endpoint.
# PeriodicExportingMetricReader specifies that metrics should be exported periodically.
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=f"{OTEL_EXPORTER_OTLP_ENDPOINT}/v1/metrics")
)
# MeterProvider manages the creation of Meters, which are used to create instruments (e.g., counters, histograms).
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
# Get a Meter instance for this application.
meter = metrics.get_meter("fastapi.ingestion.app")

# Create custom Counter instruments for tracking ingestion counts.
# Counters only go up. Attributes (labels) provide multi-dimensional data.
financial_tx_counter = meter.create_counter(
    "financial.transactions.ingested_total",
    description="Total number of financial transactions ingested",
    unit="1"
)
insurance_claim_counter = meter.create_counter(
    "insurance.claims.ingested_total",
    description="Total number of insurance claims ingested",
    unit="1"
)

# Create a custom Histogram instrument to track the duration of ingestion requests.
# Histograms allow for percentile analysis (e.g., P99 latency).
# Explicitly defined boundaries help categorize durations into meaningful buckets in Prometheus/Grafana.
ingestion_latency_histogram = meter.create_histogram(
    "ingestion.request.duration_ms",
    description="Duration of data ingestion requests in milliseconds",
    unit="ms",
    boundaries=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000] # Example buckets
)

# --- Tracing Setup ---
# OTLPSpanExporter sends traces (spans) to the configured OTLP endpoint.
trace_exporter = OTLPSpanExporter(endpoint=f"{OTEL_EXPORTER_OTLP_ENDPOINT}/v1/traces")
# TracerProvider manages the creation of Tracers, which are used to create Spans.
trace.set_tracer_provider(TracerProvider(resource=resource))
# BatchSpanProcessor asynchronously sends spans in batches to the exporter.
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(trace_exporter)
)

# --- Logging Instrumentation ---
# LoggingInstrumentor automatically injects trace_id and span_id into log records,
# making it easier to correlate logs with specific requests in a distributed trace.
LoggingInstrumentor().instrument(set_logging_format=True)

# --- Pydantic Models for Request Body Validation ---
class FinancialTransaction(BaseModel):
    transaction_id: str = Field(..., example="FT-20231026-001")
    timestamp: datetime = Field(..., example="2023-10-26T14:30:00Z")
    account_id: str = Field(..., example="ACC-001")
    amount: float = Field(..., gt=0, example=150.75)
    currency: str = Field(..., max_length=3, example="USD")
    transaction_type: str = Field(..., example="debit")
    merchant_id: Optional[str] = Field(None, example="MER-XYZ")
    category: Optional[str] = Field(None, example="groceries")

class InsuranceClaim(BaseModel):
    claim_id: str = Field(..., example="IC-20231026-001")
    timestamp: datetime = Field(..., example="2023-10-26T15:00:00Z")
    policy_number: str = Field(..., example="POL-987654")
    claim_amount: float = Field(..., gt=0, example=1000.00)
    claim_type: str = Field(..., example="auto")
    claim_status: str = Field(..., example="submitted")
    customer_id: str = Field(..., example="CUST-ABC")
    incident_date: datetime = Field(..., example="2023-09-15T08:00:00Z")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Financial/Insurance Data Ingestor API",
    description="API for ingesting various financial and insurance data into the data platform.",
    version="1.0.0",
)

# Instrument the FastAPI application with OpenTelemetry.
# This automatically creates spans for incoming HTTP requests and handles context propagation.
FastAPIInstrumentor.instrument_app(app)

# --- Kafka Producer Setup ---
# Kafka broker address and topic names are loaded from environment variables.
# In Docker Compose, 'kafka' is the service name, which resolves to its internal IP.
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:29092")
KAFKA_TOPIC_FINANCIAL = os.getenv("KAFKA_TOPIC_FINANCIAL", "raw_financial_transactions")
KAFKA_TOPIC_INSURANCE = os.getenv("KAFKA_TOPIC_INSURANCE", "raw_insurance_claims")

producer = None # Initialize producer to None
try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        retries=5,         # Number of times to retry sending a message
        linger_ms=100,      # Time to wait before sending a batch of messages
        batch_size=16384    # Maximum size of a batch of messages
    )
    print(f"Kafka Producer initialized for broker: {KAFKA_BROKER}")
except Exception as e:
    # Log the error if Kafka producer initialization fails, but don't stop the app.
    # The health check will eventually fail if Kafka is critical for app function.
    print(f"Error initializing Kafka Producer: {e}. Ingestion endpoints may not function correctly.")

# --- API Endpoints ---

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint for the FastAPI application.
    Returns a simple status to indicate if the application is running.
    """
    return {"status": "healthy", "message": "Welcome to Financial/Insurance Data Ingestor API!"}

@app.post("/ingest-financial-transaction/", status_code=status.HTTP_200_OK, tags=["Ingestion"])
async def ingest_financial_transaction(transaction: FinancialTransaction):
    """
    Ingests a financial transaction and publishes it to a Kafka topic.
    Custom OpenTelemetry metrics are incremented for each successful ingestion.
    """
    start_time = time.perf_counter_ns() # High-resolution timer for latency measurement
    try:
        if producer:
            # Send the transaction data as a JSON string to the Kafka topic
            producer.send(KAFKA_TOPIC_FINANCIAL, transaction.model_dump())
            print(f"Financial transaction ingested and sent to Kafka topic '{KAFKA_TOPIC_FINANCIAL}': {transaction.transaction_id}")
        else:
            # If producer failed to initialize, log a warning and return success for demonstration.
            # In a real app, this might be an HTTPException or a retry mechanism.
            print("Kafka producer not available. Skipping send for financial transaction.")

        # Increment the financial transaction counter with relevant attributes
        financial_tx_counter.add(1, {
            "transaction.type": transaction.transaction_type,
            "currency": transaction.currency,
            "status": "success" # Add a status attribute
        })

        return {"message": "Financial transaction ingested successfully", "transaction_id": transaction.transaction_id}
    except Exception as e:
        # If an error occurs, increment the counter with a 'failed' status
        financial_tx_counter.add(1, {
            "transaction.type": transaction.transaction_type,
            "currency": transaction.currency,
            "status": "failed"
        })
        print(f"Failed to ingest financial transaction: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to ingest transaction: {e}")
    finally:
        # Record the ingestion latency regardless of success or failure
        end_time = time.perf_counter_ns()
        duration_ms = (end_time - start_time) / 1_000_000 # Convert nanoseconds to milliseconds
        ingestion_latency_histogram.record(duration_ms, {
            "endpoint": "/ingest-financial-transaction",
            "transaction.type": transaction.transaction_type,
            "status": "completed" if producer else "failed_producer_unavailable"
        })

@app.post("/ingest-insurance-claim/", status_code=status.HTTP_200_OK, tags=["Ingestion"])
async def ingest_insurance_claim(claim: InsuranceClaim):
    """
    Ingests an insurance claim and publishes it to a Kafka topic.
    Custom OpenTelemetry metrics are incremented for each successful ingestion.
    """
    start_time = time.perf_counter_ns()
    try:
        if producer:
            # Send the claim data as a JSON string to the Kafka topic
            producer.send(KAFKA_TOPIC_INSURANCE, claim.model_dump())
            print(f"Insurance claim ingested and sent to Kafka topic '{KAFKA_TOPIC_INSURANCE}': {claim.claim_id}")
        else:
            print("Kafka producer not available. Skipping send for insurance claim.")

        # Increment the insurance claim counter with relevant attributes
        insurance_claim_counter.add(1, {
            "claim.type": claim.claim_type,
            "claim.status": claim.claim_status,
            "status": "success"
        })
        return {"message": "Insurance claim ingested successfully", "claim_id": claim.claim_id}
    except Exception as e:
        # If an error occurs, increment the counter with a 'failed' status
        insurance_claim_counter.add(1, {
            "claim.type": claim.claim_type,
            "claim.status": claim.claim_status,
            "status": "failed"
        })
        print(f"Failed to ingest insurance claim: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to ingest claim: {e}")
    finally:
        # Record the ingestion latency regardless of success or failure
        end_time = time.perf_counter_ns()
        duration_ms = (end_time - start_time) / 1_000_000
        ingestion_latency_histogram.record(duration_ms, {
            "endpoint": "/ingest-insurance-claim",
            "claim.type": claim.claim_type,
            "status": "completed" if producer else "failed_producer_unavailable"
        })
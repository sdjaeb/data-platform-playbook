# Manifest High-Performance Lab: Industrial Data Lifecycle

This lab demonstrates an industrial-grade SBOM/AIBOM ingestion and governance pipeline built for extreme scale and forensic integrity.

## 1. System Breakdown: The "Industrial Data" Lifecycle

| Stage | Component | Action | Why this matters for Manifest |
| :--- | :--- | :--- | :--- |
| **Go Ingestor** | `ingestor-go/main.go` | Receives raw CBOR/JSON. Performs **Deterministic Hashing** (SHA-256) on raw bytes to generate a CID. | Handles 100k+ TPS. Ensures forensic integrity before data is even decoded. |
| **Bronze Consumer**| `app/bronze_consumer.py`| Listens to Kafka (`raw-sboms`). Writes raw payloads to MinIO using the CID as the filename. | **Global Deduplication.** If the same SBOM is sent twice, it's caught here and not re-processed. |
| **Bronze Job** | (Implicit) | Raw data persistence in S3-compatible storage. | Preserves "the original evidence" for future audits. |
| **Silver Job** | `jobs/silver_job.py` | Uses **Polars Lazy Scanning**. Joins SBOM fragments with the `vulnerabilities.parquet` master list. | Normalized enrichment. Converts messy JSON fragments into structured, high-performance Parquet. |
| **Gold Sync** | `jobs/gold_sync.py` | Bulk-upserts results into MongoDB and **flushes the Redis cache**. | Sub-second serving. Moves data from "Processing Layer" to "Analytical Serving Layer." |
| **Mock Data** | `jobs/create_mock_data.py`| Updates the `vulnerabilities.parquet` file. | Simulates a "Patch" or a new zero-day discovery in the system. |
| **Evaluate API** | `app/api.py` | FastAPI route that queries Gold storage and sends the result to **OPA**. | Enforces governance. It doesn't just say "here is a CVE," it says "Deployment Blocked." |
| **Load Test** | `jobs/load_test.py` | Floods the Go Ingestor with 20k requests. | Proves the **Circuit Breaker** and **Backpressure** logic works under stress. |
| **OPA** | `policy.rego` | Evaluates logic like `allow if severity != "CRITICAL"`. | Decouples security policy from application code. |

---

## 2. How to Demonstrate It's Working (The "Audit Trail")

To demonstrate the "Industrial Forensic" quality of this stack, you can run a single piece of data from a binary hash to a legal verdict.

### The Audit Trace
Run the audit script to trace a component through all three Medallion layers:
```bash
uv run python labs/manifest-lab/jobs/audit_trace.py
```

### AIBOM Ingestion
Demonstrate support for AI Bill of Materials (Models, Weights, Datasets):
```bash
uv run python labs/manifest-lab/jobs/ingest_aibom.py
```

---

## 3. How this stack demonstrates "What Manifest Expects"

Manifest expects an **attestation-first** architecture. This stack delivers that in three ways:

1.  **Deduplication is Business Logic, not an Afterthought:**
    By using the CID (hash of raw bytes) in the Bronze layer, the system is "Content Addressable." If a vendor sends the same SBOM 100 times, you only pay for storage and compute once.
2.  **The "Medallion" Security Audit:**
    The system doesn't just look up a CVE. It traces **CID (Evidence)** -> **Parquet (Refinement)** -> **OPA (Policy)**. This is the foundation of "Continuous Compliance."
3.  **Governance as Code:**
    By using **Open Policy Agent (OPA)**, security teams can update policies (e.g., "Block all models trained on dataset X") without engineering teams needing to redeploy code.

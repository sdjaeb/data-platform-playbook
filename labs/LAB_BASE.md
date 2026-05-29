# Lab Base Architecture: The Golden Path

This document defines the standardized architectural patterns, folder structures, and technical standards for all labs in this repository. Every lab (Manifest, Kinimatic, Plura) aims to adhere to these principles to ensure consistency and modularity.

---

## 1. Core Architectural Pillars

### A. Hexagonal Architecture (Ports & Adapters)
- **Goal:** Decouple business logic (the "Domain") from external infrastructure (Kafka, S3, APIs).
- **Structure:**
  - `domain/`: Pure logic, models, and interfaces (Protocols).
  - `ports/`: Interface definitions for storage, messaging, and researchers.
  - `adapters/`: Concrete implementations (e.g., `S3Adapter`, `KafkaProducer`).

### B. Medallion Data Flow
- **Bronze (Raw):** Immutable landing zone. Data is stored exactly as received (JSON/CBOR).
- **Silver (Refined):** Normalized, type-safe, and joined data. Transformations are powered by **Polars (Lazy API)**.
- **Gold (Aggregated):** High-performance serving layer (MongoDB/Redis) optimized for end-user queries.

### C. Observability-First Design
- Every service must expose a `/metrics` endpoint (Prometheus).
- All logs must be structured (JSON) and include a `trace_id` to track events across the Medallion layers.

---

## 2. Standardized Lab Structure

```text
labs/<lab-name>/
├── data-generator/      # Synthetic event producers (Python)
├── src/                 # Main application code
│   ├── domain/          # Business logic & models
│   ├── infrastructure/  # Ports & Adapters implementations
│   └── main.py          # Entry point
├── jobs/                # Batch/Streaming processing scripts (Polars/Spark)
├── docker-compose.yml   # Lab-specific service overrides
└── README.md            # Lab objectives, scenarios, and AI-critique goals
```

---

## 3. Technical Standards

| Layer | Standard Tech | Rationale |
| :--- | :--- | :--- |
| **Ingestion** | Go (Goroutines) | High-concurrency, low-latency entry points. |
| **Buffering** | Kafka | Durable event log; decouples producers from consumers. |
| **Processing** | Polars (Lazy) | Memory-efficient, multi-threaded columnar transformations. |
| **Serialization** | CBOR / Arrow | Binary performance with zero-copy handoff potential. |
| **Policy** | OPA (Rego) | Decouples security/business rules from the code. |

---

## 4. AI-Augmented Workflow
Manifest and Kinimatic both value the "Augmented Engineer."
1. **Bootstrap with AI:** Use LLMs for boilerplate (Kafka configs, Dockerfiles).
2. **The Critique:** Every lab requires documentation of how the AI output was improved (e.g., "AI suggested eager loading; I implemented Lazy Polars to prevent OOM").
3. **The Guardrail:** AI is used for **implementation**, while the Principal IC owns the **architectural contract**.

---

## 5. Lab Checklist
Before a lab is considered "Complete":
- [ ] Does it have a synthetic data generator?
- [ ] Does it implement at least two layers of the Medallion architecture?
- [ ] Is there a clear separation between Domain logic and Infrastructure?
- [ ] Does it include a specific "Staff-Level Challenge" (e.g., Backpressure, Time-Travel, CAS)?

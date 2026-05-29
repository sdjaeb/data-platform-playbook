# Lab Build Prompt: Manifest (Security/High-Scale)
Reference: ../LAB_BASE.md

## Objective
Build a high-performance SBOM ingestion and vulnerability mapping pipeline.

## Architectural Requirements
1. **Hexagonal Structure:** Implement `src/domain` for SBOM models and `src/infrastructure` for Kafka/Iceberg adapters.
2. **Medallion Flow:** 
   - **Bronze:** Go-based ingestor landing CBOR/COSE signed data in S3.
   - **Silver:** Polars Lazy processing for SemVer normalization and Iceberg commits.
   - **Gold:** MongoDB + CAS (Content-Addressable Storage) for deduplicated lookups.
3. **Staff Challenge:** Implement a **Global Deduplication** check using Content-Addressable Storage (CAS) in the Bronze-to-Silver transition.

## Execution Steps
1. Initialize Go modules in `src/infrastructure/ingestor`.
2. Implement Polars transformation job in `jobs/silver_normalization.py`.
3. Configure OPA (`policy.rego`) for "Safe to Deploy" verdicts.

## AI Critique Task
Ask AI to write the Kafka producer. Documentation must explain why you rejected a standard JSON producer in favor of a CBOR-encoded one for 100k TPS efficiency.

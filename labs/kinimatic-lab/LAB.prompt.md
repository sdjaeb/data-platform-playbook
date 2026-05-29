# Lab Build Prompt: Kinimatic (Logistics/AI-Agents)
Reference: ../LAB_BASE.md

## Objective
Build an event-driven logistics intelligence layer using LangGraph agents.

## Architectural Requirements
1. **Hexagonal Structure:** Implement `src/domain` for Order/Inventory entities and `src/infrastructure` for EventBridge/Postgres adapters.
2. **Medallion Flow:**
   - **Bronze:** Python/Flask entry point landing raw EDI/WMS events in MinIO.
   - **Silver:** Polars-based reconciliation of 'Shipment' vs 'Inventory' events.
   - **Gold:** PostgreSQL tables optimized for LangGraph state persistence.
3. **Staff Challenge:** Implement a **LangGraph State Machine** that detects stuck shipments and triggers a re-optimization event.

## Execution Steps
1. Create `data-generator/gen_logistics.py` to simulate EDI failures.
2. Implement the normalization logic in `jobs/silver_reconciliation.py`.
3. Design the LangGraph agent in `src/domain/agents.py`.

## AI Critique Task
Ask AI to design the LangGraph nodes. Documentation must explain how you modified the AI output to ensure idempotency when an LLM-agent retries a logistics optimization task.

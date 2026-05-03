# LAB: AI Safety & Governance Proxy (The BioTechCorp "Boss Fight")

## Objective
Build a "Safety Harness" for an LLM that demonstrates the 3 key gaps identified by the BioTechCorp Hiring Manager: **LLM Behavior/Risk**, **Model Evaluation**, and **Systems Driven by ML**.

## The Scenario
You are building an internal API for a BioTech company. The AI must summarize patient data, but it *must* follow a strict schema and *must not* include PII (mocked).

## Requirements

### 1. The "Harness" (FastAPI + Pydantic)
- Create a FastAPI endpoint `POST /analyze`.
- Use **Pydantic** to define a strict output schema (e.g., `{"summary": str, "risk_level": int, "recommended_action": str}`).
- Implement a **Guardrail Middleware**: If the LLM output is not valid JSON or doesn't match the schema, the proxy returns a 502 "Safety Violation" instead of raw garbage.

### 2. The "Risk Mitigation" (PII Scrubber)
- Implement a simple logic layer (using Regex or a library like `presidio-analyzer`) that scans the LLM response for simulated SSNs or Phone Numbers.
- If PII is detected, the request is **blocked and logged** as a security event.

### 3. The "Evaluation Suite" (Simple RAGAS-style test)
- Create a `test_suite.py` that contains a "Golden Dataset" (Input vs. Expected Output).
- Use a similarity metric (e.g., `SequenceMatcher` or a small embeddings model) to compare the LLM's summary against the Golden version.
- **Goal:** Prove you can "quantify" model performance.

### 4. The "Orchestration" (Resilience)
- Treat the LLM (Ollama) as a flaky third-party service.
- Implement a **Retry-with-Backoff** strategy using a library like `tenacity` or a simple decorator.
- Implement a **Circuit Breaker**: If Ollama fails 3 times, the system falls back to a "Dumb" template-based response to maintain system availability.

## Deliverables
- `app/safety_proxy.py`: The FastAPI harness.
- `scripts/evaluate_drift.py`: The evaluation script.
- `README.md`: A 3-sentence summary of how this handles "Non-deterministic AI" in a "Deterministic Architecture."

## Why This Wins the Interview
When the HM asks about "Model Evaluation," you don't say "I've read about it." You say: **"I built a CI/CD-integrated evaluation script that measures semantic drift against a golden dataset and fails the build if accuracy drops."**

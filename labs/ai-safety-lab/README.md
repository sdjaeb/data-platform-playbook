# AI Safety & Governance Intelligence Layer

This system bridges the gap between non-deterministic LLM outputs and deterministic enterprise requirements by enforcing strict Pydantic schema validation and PII scrubbing at the middleware layer. It implements architectural resilience using circuit breakers and exponential backoff to ensure high availability even when the underlying model service is unstable. A dedicated evaluation suite quantifies model performance against a golden dataset, enabling automated detection of semantic drift and performance degradation in CI/CD pipelines.

## 🚀 Key Features

### 1. Agentic Self-Correction (NOS Engine)
Built with **LangGraph**, the Network Optimization Engine (NOS) uses a state machine to detect "Operational Hallucinations" (e.g., routing orders to out-of-stock warehouses). If a safety audit fails, the agent automatically loops back to the LLM node with corrected context, ensuring reliable outcomes before data reaches production systems.

### 2. Deterministic Safety Harness (Middleware)
A formal **FastAPI Middleware** layer acts as an automated "Safe-by-Design" gatekeeper. It intercepts all LLM responses to perform:
- **PII Scrubbing**: Leveraging **Microsoft Presidio** for enterprise-grade detection of names, emails, and SSNs.
- **Schema Enforcement**: Strict **Pydantic** validation to prevent "raw garbage" or non-conforming JSON outputs.
- **Resilience**: Integrated **Circuit Breaking** and exponential backoff to maintain system availability during LLM service outages.

### 3. CI/CD Model Evaluation
An "Official Test Suite" containing a **Golden Dataset** (Input vs. Expected Output). It quantifies model performance using semantic similarity metrics (SequenceMatcher), allowing teams to "fail the build" if accuracy drops below the 80% threshold.

## 🛠️ Key Technologies

- **Core Framework**: Python 3.13+, FastAPI, Pydantic v2
- **Agentic Orchestration**: LangGraph, LangChain
- **Safety & Risk Mitigation**: Microsoft Presidio (PII Analyzer), Tenacity (Resilience Patterns)
- **Testing & Validation**: Pytest, HTTPX, difflib
- **Model Interface**: Optimized for local (Ollama) or cloud (Anthropic/OpenAI) providers.

## 🧪 Quick Start & Testing

Ensure you have the dependencies and the necessary spaCy model installed:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run the full validation suite
pytest -v tests/

# Run the semantic drift evaluation
python scripts/test_suite.py
```

## 🧠 Philosophy: Non-Deterministic AI in Deterministic Architecture
In high-stakes domains like BioTech and Logistics, AI cannot be allowed to operate without supervision. This project demonstrates a **Principal Engineer-level pattern** for wrapping LLMs in code that is deterministic, testable, and resilient. We treat the LLM as a high-risk, "flaky" third-party dependency that must be audited and corrected by the system at runtime.

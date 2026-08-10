# AI Safety & Governance Intelligence Layer

This reference lab wraps non-deterministic output with schema and privacy
checks. Its demonstration evaluator measures exact and lexical agreement
against versioned fixtures; it does not establish semantic or domain
correctness without calibrated human review.

## 🚀 Key Features

### 1. Agentic Self-Correction (NOS Engine)
Built with **LangGraph**, the Network Optimization Engine (NOS) uses a state machine to detect "Operational Hallucinations" (e.g., routing orders to out-of-stock warehouses). If a safety audit fails, the agent automatically loops back to the LLM node with corrected context, ensuring reliable outcomes before data reaches production systems.

### 2. Deterministic Safety Harness (Middleware)
A formal **FastAPI Middleware** layer acts as an automated "Safe-by-Design" gatekeeper. It intercepts all LLM responses to perform:
- **PII Scrubbing**: Leveraging **Microsoft Presidio** for enterprise-grade detection of names, emails, and SSNs.
- **Schema Enforcement**: Strict **Pydantic** validation to prevent "raw garbage" or non-conforming JSON outputs.
- **Resilience**: Integrated **Circuit Breaking** and exponential backoff to maintain system availability during LLM service outages.

### 3. CI/CD Model Evaluation
The fixture set separates development and held-out cases and includes negative
privacy and malformed-output scenarios. `SequenceMatcher` is a lexical
demonstration metric; the 80% lab threshold requires domain-owner calibration.

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
This lab demonstrates deterministic wrappers and failure scenarios. It is a
reference exercise, not production or compliance evidence. See
`EVALUATION_LINEAGE.md` for promotion requirements.

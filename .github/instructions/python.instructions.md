---
description: "Python backend & tests"
applyTo: "**/*.py,**/tests/**"
---

## Python Backend Rules

- Use type hints.
- Use Ruff-compatible formatting. Do not leave unused imports.
- Keep HTTP handlers thin. Put business logic in services or domain modules.
- Use explicit request and response models when the framework supports them.
- Use structured errors. Do not hide failure modes behind generic exceptions.
- Use retries only at real I/O boundaries. Prefer exponential backoff.
- Keep queue and event handlers idempotent.
- Add focused tests for changed behavior.
- Prefer deterministic fixtures. Mark slow or integration tests explicitly.
- If the repo already has a framework pattern, use it. Do not invent a new one.

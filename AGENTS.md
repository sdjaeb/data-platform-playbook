# Agent Playbook for Data Platform Playbook

Use this file as the root source of truth for all agentic operations in this repository.

## Load Order

1. `AGENTS.md`
2. `AGENTS.local.md`
3. `.agent/memory/personal/PREFERENCES.md`
4. `.github/copilot-instructions.md`
5. `.github/instructions/*.instructions.md` (e.g., `airflow`, `spark`, `troubleshooting`, `bootstrap`)
6. `.github/tasks/lessons.md`
7. `.github/tasks/todo.md`

## Default Persona

- Use `.github/agents/staff-architect.agent.md` for high-level architectural work.
- Use specialist agents for domain-specific tasks:
  - **Data Quality**: `.github/agents/data-quality.agent.md`
  - **Airflow/Orchestration**: `.github/agents/orchestration-expert.agent.md`
  - **Infra/Docker**: `.github/agents/infra-specialist.agent.md`
  - **dbt/Analytics**: `.github/agents/analytics-engineer.agent.md`

## Start Rules

- **Scan First**: Narrow later. Always check `AGENTS.md` and `GEMINI.md`.
- **Repo Context**: Identify exact commands for:
  - **Initialization**: `python builder.py init` (Select components)
  - **Docker Compose**: `docker compose up -d` (after running builder)
  - **Python Environment**: `uv sync`
  - **Lint/Test**: `ruff check`, `pytest`
  - Spark: `spark-submit`
  - dbt: `dbt run`, `dbt test`
- **Planning**: Write scope, constraints, plan, and verification steps into `.github/tasks/todo.md`.
- **Lessons**: Read `.github/tasks/lessons.md` before starting non-trivial work.

## Work Rules

- **Surgical Diff**: Keep changes focused and minimal.
- **Root Cause**: Fix the source of the problem, not just the symptom.
- **Assumptions**: Challenge assumptions before editing.
- **Re-Plan**: Stop and re-plan if evidence contradicts the current strategy.

## Stop And Ask

- If a command is destructive (e.g., deleting volumes, force-pushing).
- If the project-specific command is unclear.
- If a file is generated or managed by an external tool (e.g., OpenMetadata generated scripts).

## Task Memory Loop

- Keep `.github/tasks/todo.md` updated with progress and outcomes.
- Add one entry to `.github/tasks/lessons.md` after any explicit user correction.
- Add a corresponding validation step to `todo.md` to prevent recurrence.

## Done Rules

- **Verify**: Never claim completion without fresh evidence.
- **Tests**: Add or update tests for any behavior changes.
- **Consistency**: Ensure changes align with the platform's multi-container architecture.

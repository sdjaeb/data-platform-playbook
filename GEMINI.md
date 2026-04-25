# Gemini CLI Entry Point

This project follows **Agentic Baseline V3.1** principles.

## Operational Directives

- **Primary Source of Truth**: Read `AGENTS.md` before starting any task.
- **Workflow**: 
  1. Follow the Load Order defined in `AGENTS.md`.
  2. Use `.github/tasks/todo.md` for all non-trivial planning.
  3. Consult `.github/tasks/lessons.md` for project-specific pitfalls.
- **Tooling**: Prefer project-native commands found in `platform-core/` and `scripts/`.

## Core Project Context

- **Platform Architecture**: A containerized enterprise data platform including Airflow, Spark, dbt, OpenMetadata, and Grafana.
- **Key Directories**:
  - `platform-core/`: Docker Compose configurations.
  - `airflow_dags/`: Orchestration logic.
  - `pyspark_jobs/`: Data processing jobs.
  - `dbt_projects/`: SQL transformations.
  - `fastapi_app/`: Ingestion service.

Refer to `AGENTS.md` for detailed behavioral rules.

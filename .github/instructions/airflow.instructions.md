---
description: "Airflow DAGs and Orchestration"
applyTo: "**/airflow_dags/**/*.py,**/dags/**/*.py"
---

## Airflow Rules

- **Idempotency**: All tasks must be idempotent. Re-running a task should have no side effects if the data is already there.
- **Sensors**: Use sensors to wait for data arrival instead of hardcoded sleeps.
- **Connections**: Use Airflow Connections and Variables. Do not hardcode credentials in DAGs.
- **Operators**: Prefer `SparkSubmitOperator` or `DockerOperator` for heavy lifting. Keep the Airflow worker light.
- **Testing**: Use `dag.test()` or equivalent for local DAG validation.

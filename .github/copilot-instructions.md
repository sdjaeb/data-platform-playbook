# Repository-Wide Instructions

## Standards

- **Language**: Python 3.10+, SQL (dbt), Shell (Bash).
- **Styling**: PEP 8 for Python, standard SQL for dbt.
- **Documentation**: Keep `README.md` and `docs/` updated.

## Implementation Rules

- **Containerization**: Everything runs in Docker. Always consider the network and volume implications.
- **Environment**: Use `.env` files for configuration. Do not hardcode secrets.
- **Logging**: Use structured logging. Integrate with the observability stack (Grafana/Promtail/Loki) where possible.
- **Verification**: Verify changes by running the relevant service in Docker and checking logs or outputs.

## Project Structure

- `platform-core/`: The "engine room". Contains multiple `docker-compose.*.yml` files for modular startup.
- `data-generators/`: Services that produce synthetic data for testing.
- `openmetadata_ingestion_scripts/`: Configuration for metadata harvesting.

## Verification Checklist

- [ ] Does the change break container orchestration?
- [ ] Are the new dependencies added to the correct `requirements.txt` or `Dockerfile`?
- [ ] Is there a new lesson to be learned and documented?
- [ ] Have the relevant `docker-compose` services been restarted and verified?

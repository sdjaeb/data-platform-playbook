# Data Platform Bootstrap Skill

## Overview
Guidelines for initializing the platform from a clean state.

## Bootstrap Sequence

### Phase 1: Infrastructure Base
1. **Network & Storage**: Bring up the base network and core database (Postgres/MinIO).
   - Command: `docker-compose -f platform-core/docker-compose.base.yml up -d`
2. **Persistence**: Verify volumes are correctly mounted in `data/`.

### Phase 2: Orchestration & Ingestion
1. **Airflow**: Initialize the metadata database and bring up the webserver/scheduler.
   - Command: `docker-compose -f platform-core/docker-compose.orchestration.yml up -d`
2. **FastAPI**: Start the ingestion service.
   - Command: `docker-compose -f platform-core/docker-compose.ingestion.yml up -d`

### Phase 3: Processing & Transformation
1. **Spark**: Start the Spark Master and Workers.
   - Command: `docker-compose -f platform-core/docker-compose.processing.yml up -d`
2. **dbt**: Verify dbt connectivity to the data warehouse.
   - Command: `dbt debug` (run from `dbt_projects/`)

### Phase 4: Governance & Observability
1. **OpenMetadata**: Bring up the governance stack.
   - Command: `docker-compose -f platform-core/docker-compose.governance.yml up -d`
2. **Grafana/Prometheus**: Start the observability suite.
   - Command: `docker-compose -f platform-core/docker-compose.observability.yml up -d`

## Post-Bootstrap Verification
- [ ] Airflow UI accessible at `localhost:8080`.
- [ ] Spark Master UI accessible at `localhost:8081`.
- [ ] MinIO UI accessible at `localhost:9001`.
- [ ] OpenMetadata UI accessible at `localhost:8585`.
- [ ] FastAPI Swagger docs at `localhost:8000/docs`.

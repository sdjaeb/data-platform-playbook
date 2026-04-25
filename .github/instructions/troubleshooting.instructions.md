# Platform Troubleshooting Skill

## Overview
This skill provides diagnostic patterns and fixes for the `data-platform-playbook` containerized environment.

## Common Failure Modes

### 1. Spark Executor OOM
- **Symptoms**: `pyspark_jobs` failing with "Container killed by YARN for exceeding memory limits" or "Executor lost".
- **Check**: `docker logs spark-master` and `docker logs spark-worker`.
- **Fix**: 
  - Increase `spark.executor.memory` in `platform-core/docker-compose.processing.yml`.
  - Check for data skew in the transformation logic.

### 2. Airflow Database Locking
- **Symptoms**: DAGs stuck in "queued" or "running" but no tasks starting.
- **Check**: `docker logs airflow-scheduler`. Look for "Database is locked" or "Max active runs reached".
- **Fix**: 
  - Restart the scheduler: `docker-compose -f platform-core/docker-compose.orchestration.yml restart airflow-scheduler`.
  - Check `AIRFLOW__DATABASE__SQL_ALCHEMY_POOL_SIZE` in `platform-core/config/airflow.cfg`.

### 3. MinIO Connectivity (S3 Endpoint)
- **Symptoms**: Spark or Airflow failing with "Connection Refused" to `minio:9000`.
- **Check**: `docker inspect minio` for network alias.
- **Fix**: Ensure the calling service is on the same Docker network as MinIO (usually `platform-network`).

### 4. dbt Compilation Errors
- **Symptoms**: `dbt run` failing during the compilation phase.
- **Check**: `dbt_projects/logs/dbt.log`.
- **Fix**: 
  - Check `dbt_profiles/profiles.yml` for correct credentials and schema.
  - Verify that the target database (Postgres/Snowflake) is reachable.

## Troubleshooting Protocol
1. **Identify**: Which service is failing? (Use `docker ps`).
2. **Inspect**: Check logs for that specific container.
3. **Isolate**: Is it a code bug or an infra issue (connectivity/resources)?
4. **Fix**: Apply the minimal change (config or code).
5. **Verify**: Restart the service and monitor logs.

# Data Flow Verification Cheatsheet (with Advanced CLI Tips)

This document provides a comprehensive set of CLI commands and explanations for verifying data flow, service health, and advanced troubleshooting within the `platform-core` environment.  
**All commands assume you are running from your project root and Docker Compose services are up.**

---

## 1. Kafka: Data Ingestion, Status, and Advanced Inspection

### Basic

- **List all Kafka topics:**  
  See which topics exist in your Kafka broker.
  ```bash
  docker exec -it kcat kcat -b kafka:9092 -L
  ```

- **Consume messages from a topic:**  
  View live data as it arrives on a topic (replace topic as needed).
  ```bash
  docker run --rm -it --network platform-core_data_platform_network edenhill/kcat:1.7.1 \
    -b kafka:29092 -t raw_sports_events -C -J
  ```

### Advanced

- **Describe a topic:**  
  Get partition count, offsets, and configuration for a topic.
  ```bash
  docker exec -it kafka kafka-topics --bootstrap-server localhost:29092 --describe --topic <topic_name>
  ```

- **List all consumer groups:**  
  See which consumer groups are registered with Kafka.
  ```bash
  docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:29092 --list
  ```

- **Describe a consumer group:**  
  Check lag, partition assignment, and member info for a group.
  ```bash
  docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:29092 --describe --group <group_name>
  ```

---

## 2. MinIO: Data Lake Contents and Health

### Basic

- **List all buckets:**  
  See all S3 buckets in your MinIO instance.
  ```bash
  docker run --network platform-core_data_platform_network --rm \
    -e "MC_HOST_myminio=http://$(cat ./secrets/minio_user.txt):$(cat ./secrets/minio_pass.txt)@minio:9000" \
    minio/mc ls myminio
  ```

- **List contents of a bucket:**  
  View files and folders in a specific bucket.
  ```bash
  docker run --network platform-core_data_platform_network --rm \
    -e "MC_HOST_myminio=http://$(cat ./secrets/minio_user.txt):$(cat ./secrets/minio_pass.txt)@minio:9000" \
    minio/mc ls myminio/raw-data-bucket
  ```

- **View a sample file:**  
  Output the contents of a file (e.g., Parquet) from MinIO.
  ```bash
  docker run --network platform-core_data_platform_network --rm \
    -e "MC_HOST_myminio=http://$(cat ./secrets/minio_user.txt):$(cat ./secrets/minio_pass.txt)@minio:9000" \
    minio/mc cat myminio/raw-data-bucket/financial_data_delta/part-00000-some-uuid.snappy.parquet | head
  ```

### Advanced

- **Check MinIO server health:**  
  Returns HTTP 200 if MinIO is live (if healthcheck is enabled).
  ```bash
  curl http://localhost:9900/minio/health/live
  ```

- **Get MinIO server info:**  
  Shows server status, uptime, and configuration.
  ```bash
  docker exec -it minio mc admin info myminio
  ```

---

## 3. PostgreSQL: Metadata, Application Data, and Performance

### Basic

- **Connect to a database:**  
  Example for Airflow:
  ```bash
  docker exec -it postgres psql -U airflow -d airflow
  ```

- **List tables and view recent DAG runs:**  
  Inside `psql`:
  ```sql
  \dt;
  SELECT dag_id, state, execution_date FROM dag_run ORDER BY execution_date DESC LIMIT 5;
  \q
  ```

### Advanced

- **Show active connections:**  
  See who/what is connected to your database.
  ```sql
  SELECT datname, usename, client_addr, state FROM pg_stat_activity;
  ```

- **Show table sizes:**  
  Find out which tables use the most space.
  ```sql
  SELECT relname AS "Table", pg_size_pretty(pg_total_relation_size(relid)) AS "Size"
  FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC;
  ```

---

## 4. Airflow: DAGs, Health, and Logs

### Basic

- **List all DAGs:**
  ```bash
  docker exec -it airflow-webserver airflow dags list
  ```

- **Check Airflow webserver health:**
  ```bash
  curl http://localhost:8080/health
  ```

### Advanced

- **List DAG runs for a specific DAG:**
  ```bash
  docker exec -it airflow-webserver airflow dags list-runs -d <dag_id>
  ```

- **Trigger a DAG manually:**
  ```bash
  docker exec -it airflow-webserver airflow dags trigger <dag_id>
  ```

- **Check Airflow scheduler logs:**
  ```bash
  docker logs airflow-scheduler
  ```

---

## 5. Spark: Job Status, History, and Logs

### Basic

- **Spark Master UI:**  
  View active and completed jobs at [http://localhost:8081](http://localhost:8081)

- **Spark History Server UI:**  
  Browse logs and completed job details at [http://localhost:18080](http://localhost:18080)

### Advanced

- **List running Spark jobs (JSON):**
  ```bash
  curl http://localhost:8081/json | jq '.activeapps'
  ```

- **Check Spark worker logs:**
  ```bash
  docker logs spark-worker-1
  docker logs spark-worker-2
  ```

---

## 6. OpenMetadata: Metadata, Health, and Pipelines

### Basic

- **OpenMetadata UI:**  
  [http://localhost:8585](http://localhost:8585)

- **Healthcheck endpoint:**  
  ```bash
  curl http://localhost:8586/healthcheck
  ```

### Advanced

- **Check ingestion pipeline status (inside container):**
  ```bash
  docker exec -it openmetadata-server curl -s http://localhost:8586/api/v1/services/ingestionPipelines | jq
  ```

- **Check OpenMetadata logs:**
  ```bash
  docker logs openmetadata-server
  ```

---

## 7. Spline: Lineage and API

### Basic

- **Spline UI:**  
  [http://localhost:9090](http://localhost:9090)

### Advanced

- **Check Spline REST API status:**
  ```bash
  curl http://localhost:8080/health
  ```

- **List all lineage events (if API is available):**
  ```bash
  curl http://localhost:8080/producer/executions
  ```

---

## 8. General Docker Compose Health and Logs

- **List all services and health status:**
  ```bash
  docker compose -f platform-core/docker-compose.orchestration.yml ps
  ```

- **Show container resource usage (CPU, MEM):**
  ```bash
  docker stats
  ```

- **Show logs for a specific service (last 100 lines):**
  ```bash
  docker logs --tail 100 <container_name>
  ```

---

**Tip:**  
Replace placeholder values (like `<topic_name>`, `<group_name>`, `<dag_id>`, `<collection_name>`, `<container_name>`) with your actual resource names.

---

This cheatsheet is designed to help you quickly verify, inspect, and troubleshoot every major component in your data platform using the CLI.
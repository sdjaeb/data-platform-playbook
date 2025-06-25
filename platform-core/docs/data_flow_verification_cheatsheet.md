# Data Flow Verification Cheatsheet

This document provides a collection of useful command-line interface (CLI) commands to verify data flow and service health within the `platform-core` environment. These commands are executed from your host machine's terminal, typically using `docker exec` to interact with containers or `docker run` for ephemeral tools.

Before running these commands, ensure your Docker Compose services are up and running:
`docker compose up -d`

---

## 1. Kafka: Verify Data Ingestion and Topic Status

The data generators (financial, insurance, sports) send data to Kafka topics. Use `kcat` (Kafka Cat) inside the `kafka` container to inspect these topics.

**Check if Kafka topics exist:**
```bash
docker exec -it kafka kafka-topics --bootstrap-server localhost:29092 --list
```
*Expected output includes `raw_financial_transactions`, `raw_insurance_claims`, `raw_sports_events`.*

**Listen to `raw_financial_transactions` (Financial Data):**
```bash
docker exec -it kafka kcat -b localhost:29092 -t raw_financial_transactions -C -J
```
*This command will continuously print JSON messages as they arrive. Press `Ctrl+C` to stop.*

**Listen to `raw_insurance_claims` (Insurance Data):**
```bash
docker exec -it kafka kcat -b localhost:29092 -t raw_insurance_claims -C -J
```

**Listen to `raw_sports_events` (Sports Data):**
```bash
docker exec -it kafka kcat -b localhost:29092 -t raw_sports_events -C -J
```

---

## 2. MinIO: Inspect Data Lake Contents

MinIO acts as your S3-compatible data lake. Use the `mc` (MinIO Client) tool to interact with it. For these commands, we'll pass credentials directly to avoid persistent alias setup.

**List all MinIO buckets:**
```bash
docker run --network platform-core_data_platform_network --rm \
  -e "MC_HOST_myminio=http://$(cat ./secrets/minio_user.txt):$(cat ./secrets/minio_pass.txt)@minio:9000" \
  minio/mc ls myminio
```
*Expected output includes `raw-data-bucket` and `curated-data-bucket`.*

**List contents of `raw-data-bucket`:**
```bash
docker run --network platform-core_data_platform_network --rm \
  -e "MC_HOST_myminio=http://$(cat ./secrets/minio_user.txt):$(cat ./secrets/minio_pass.txt)@minio:9000" \
  minio/mc ls myminio/raw-data-bucket
```
*You should see subdirectories like `financial_data_delta/` if Spark streaming is writing data.*

**List contents of `curated-data-bucket`:**
```bash
docker run --network platform-core_data_platform_network --rm \
  -e "MC_HOST_myminio=http://$(cat ./secrets/minio_user.txt):$(cat ./secrets/minio_pass.txt)@minio:9000" \
  minio/mc ls myminio/curated-data-bucket
```
*You should see subdirectories like `financial_data_curated_full_pipeline/` after Spark batch transformations run.*

**View a sample file from MinIO (replace with an actual file path):**
```bash
# First, find a file (e.g., a Parquet file):
# docker run --network platform-core_data_platform_network --rm \
#   -e "MC_HOST_myminio=http://$(cat ./secrets/minio_user.txt):$(cat ./secrets/minio_pass.txt)@minio:9000" \
#   minio/mc ls --recursive myminio/raw-data-bucket/financial_data_delta/

# Then, use the full path to view its content (Parquet files are binary, so `head` will show some binary data)
docker run --network platform-core_data_platform_network --rm \
  -e "MC_HOST_myminio=http://$(cat ./secrets/minio_user.txt):$(cat ./secrets/minio_pass.txt)@minio:9000" \
  minio/mc cat myminio/raw-data-bucket/financial_data_delta/part-00000-some-uuid.snappy.parquet | head
```

---

## 3. MongoDB: Query Raw Ingested Data

The FastAPI ingestor also sends raw data to MongoDB.

**Connect to the MongoDB shell:**
```bash
docker exec -it mongodb mongosh
```
*Once connected, you'll be in the `mongosh` prompt.*

**Inside `mongosh`:**
*   **List databases:**
    ```javascript
    show dbs;
    ```
    *Look for `fastapi_ingestor_db`.*
*   **Switch to the ingestor database:**
    ```javascript
    use fastapi_ingestor_db;
    ```
*   **List collections in the database:**
    ```javascript
    show collections;
    ```
    *Look for `financial_transactions`, `insurance_claims`, `sports_events`.*
*   **View a sample document from `financial_transactions`:**
    ```javascript
    db.financial_transactions.find().limit(1).pretty();
    ```
    *This will display one document in a readable JSON format.*
*   **Exit `mongosh`:**
    ```javascript
    exit
    ```

---

## 4. PostgreSQL: Inspect Metadata and Application Data

PostgreSQL is used by Airflow (metadata), Superset (metadata), and potentially dbt (metadata).

**Connect to Airflow's PostgreSQL database:**
```bash
docker exec -it postgres psql -U airflow -d airflow
```
*You'll be prompted for the password, which is `airflow` by default.*

**Inside `psql` (for Airflow DB):**
*   **List tables:**
    ```sql
    \dt;
    ```
*   **View recent DAG runs:**
    ```sql
    SELECT dag_id, state, execution_date FROM dag_run ORDER BY execution_date DESC LIMIT 5;
    ```
*   **Exit `psql`:**
    ```sql
    \q
    ```

**Connect to Superset's PostgreSQL database:**
```bash
docker exec -it postgres psql -U $(cat ./secrets/superset_db_user.txt) -d superset
```
*You'll be prompted for the password, which is in `./secrets/superset_db_pass.txt`.*

**Connect to dbt's PostgreSQL metadata database:**
```bash
docker exec -it postgres psql -U $(cat ./secrets/dbt_db_user.txt) -d dbt_metadata
```
*You'll be prompted for the password, which is in `./secrets/dbt_db_pass.txt`.*

---

## 5. Spark: Check UI for Job Status and History

While direct CLI commands for Spark job output are complex, the UIs provide excellent visibility.

*   **Spark Master UI:** `http://localhost:8081`
    *   View active applications, workers, and completed jobs.
*   **Spark History Server UI:** `http://localhost:18080`
    *   Browse logs and details for completed Spark jobs.

---

## 6. OpenMetadata & Spline: Explore Lineage and Metadata

These services provide rich UIs for data governance.

*   **OpenMetadata UI:** `http://localhost:8585`
    *   Explore ingested metadata, search for data assets, and view data profiles.
*   **Spline UI:** `http://localhost:9090`
    *   Visualize data lineage graphs for Spark jobs.
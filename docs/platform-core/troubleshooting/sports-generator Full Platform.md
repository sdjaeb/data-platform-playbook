# Data Flow Debug Checklist (Sports Generator Only)

This guide helps you trace and debug the data flow from the `sports-generator` through Kafka, Spark, MinIO (Delta Lake), and downstream systems in your platform.  
Use these CLI commands and browser URLs to pinpoint where data may be getting stuck.

---

## 1. Sports Data Generator

- **Check generator logs for successful sends:**
  ```sh
  docker logs sports-generator
  ```
- **Manually trigger data generation (if supported):**
  ```sh
  curl http://localhost:5003/start
  ```

---

## 2. Kafka

- **List all topics to confirm your topic exists:**
  ```sh
  docker exec kafka kafka-topics --bootstrap-server localhost:29092 --list
  ```
- **Consume messages from the sports topic to verify data arrival:**
  ```sh
  docker run --rm -it --network platform-core_data_platform_network edenhill/kcat:1.7.1 \
    -b kafka:29092 -t raw_sports_events -C -J
  ```
- **Check Kafka logs for errors:**
  ```sh
  docker logs kafka
  ```

---

## 3. Spark Streaming/Batch Jobs

- **Check Spark Master UI for running/completed jobs:**
  - [http://localhost:8081](http://localhost:8081)
- **Check Spark History Server for completed jobs:**
  - [http://localhost:18080](http://localhost:18080)
- **Check Spark worker logs for errors:**
  ```sh
  docker logs spark-master
  docker logs spark-worker-1
  docker logs spark-worker-2
  ```

---

## 4. MinIO (Delta Lake Storage)

- **Access MinIO UI to browse files:**
  - [http://localhost:9001](http://localhost:9001)  
    *(User: `minioadmin`, Pass: `minioadmin`)*
- **List files in the raw and curated data buckets:**
  ```sh
  docker exec minio mc ls local/raw-data-bucket
  docker exec minio mc ls local/curated-data-bucket
  ```
- **Check MinIO logs for errors:**
  ```sh
  docker logs minio
  ```

---

## 5. OpenMetadata & Spline (Lineage & Metadata)

- **OpenMetadata UI:**  
  [http://localhost:8585](http://localhost:8585)
- **Spline UI:**  
  [http://localhost:9090](http://localhost:9090)
- **Check OpenMetadata logs:**
  ```sh
  docker logs openmetadata-server
  ```
- **Check Spline logs:**
  ```sh
  docker logs spline-rest
  ```

---

## 6. Airflow (Orchestration & Monitoring)

- **Airflow UI:**  
  [http://localhost:8080](http://localhost:8080)
- **Check DAG/task logs for failures or retries.**
- **Airflow webserver/scheduler logs:**
  ```sh
  docker logs airflow-webserver
  docker logs airflow-scheduler
  ```

---

## 7. General Docker Compose Health

- **Check all service statuses:**
  ```sh
  docker compose -f platform-core/docker-compose.orchestration.yml ps
  ```
- **Look for unhealthy or restarting containers.**

---

## Troubleshooting Tips

- **Work step-by-step:**  
  If data is in Kafka but not in MinIO, focus on Spark. If it’s in MinIO but not in downstream systems, focus on the next pipeline stage.
- **Check logs for errors or stack traces at each step.**
- **Use browser UIs for Spark, MinIO, Airflow, OpenMetadata, and Spline for visual inspection.**

---

**If you find where the data stops flowing, check the logs for that component and review configuration or pipeline code as needed.**
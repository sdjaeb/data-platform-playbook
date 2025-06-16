#!/bin/bash

# bootstrap.sh - Comprehensive Bootstrap Script for Local Enterprise Data Platform
# This script automates the setup of the full data platform local environment.
# It performs prerequisite checks, sets up project directories, brings up all
# Docker Compose services, initializes key data components (Kafka, MinIO, Airflow DB),
# and provides access URLs.

echo "--- Starting Enterprise Data Platform Local Environment Setup ---"

# --- 1. Prerequisites Check ---
echo "--- Checking Prerequisites ---"
# Check for Docker and Docker Compose
command -v docker >/dev/null 2>&1 || { echo >&2 "Error: Docker is required but not installed. Aborting."; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo >&2 "Error: Docker Compose (v2.x) is required but not installed. Aborting."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo >&2 "Error: Python3 is required but not installed. Aborting."; exit 1; }
command -v nc >/dev/null 2>&1 || { echo >&2 "Warning: 'nc' (netcat) is recommended for health checks but not installed. Proceeding anyway."; }
command -v curl >/dev/null 2>&1 || { echo >&2 "Warning: 'curl' is recommended for health checks but not installed. Proceeding anyway."; }

# Check for Locust if planning to run load tests
if ! command -v locust >/dev/null 2>&1; then
  echo "Warning: Locust (for load testing) is not installed. You can install it later with 'pip install locust'."
fi

echo "All essential prerequisites appear to be met."

# --- 2. Project Directory Setup ---
echo "--- Setting up project directories ---"
mkdir -p data/{postgres,mongodb,minio,spark-events,grafana,airflow_logs,openmetadata_mysql,openmetadata_elasticsearch,spline_jars}
mkdir -p fastapi_app/app
mkdir -p pyspark_jobs
mkdir -p airflow_dags
mkdir -p observability/{grafana_dashboards,grafana_datasources}
mkdir -p openmetadata_ingestion_scripts
mkdir -p webhook_listener_app

# Create dummy files/directories if they don't exist, as required by docker-compose mounts
touch ./observability/alloy-config.river # Ensure this file exists for Grafana Alloy mount
touch ./fastapi_app/requirements.txt # Ensure requirements.txt exists for FastAPI build
touch ./webhook_listener_app/requirements.txt # Ensure requirements.txt exists for webhook listener build
touch ./webhook_listener_app/app.py # Ensure app.py exists for webhook listener build

echo "Project directories created."

# --- 3. Download External Dependencies (Spline JARs) ---
echo "--- Downloading Spline JARs (if not already present in data/spline_jars) ---"
SPLINE_JARS_DIR="./data/spline_jars"
SPLINE_AGENT_URL="https://repo1.maven.org/maven2/za/co/absa/spline/spline-agent-bundle_2.12/0.7.1/spline-agent-bundle_2.12-0.7.1.jar"
SPLINE_SPARK_AGENT_BUNDLE_URL="https://repo1.maven.org/maven2/za/co/absa/spline/spline-spark-agent-bundle_2.12/0.7.1/spline-spark-agent-bundle_2.12-0.7.1.jar"

if [ ! -f "${SPLINE_JARS_DIR}/spline-agent-bundle_2.12-0.7.1.jar" ]; then
    echo "Downloading spline-agent-bundle_2.12-0.7.1.jar..."
    curl -L -o "${SPLINE_JARS_DIR}/spline-agent-bundle_2.12-0.7.1.jar" "$SPLINE_AGENT_URL"
else
    echo "spline-agent-bundle_2.12-0.7.1.jar already exists."
fi

if [ ! -f "${SPLINE_JARS_DIR}/spline-spark-agent-bundle_2.12-0.7.1.jar" ]; then
    echo "Downloading spline-spark-agent-bundle_2.12-0.7.1.jar..."
    curl -L -o "${SPLINE_JARS_DIR}/spline-spark-agent-bundle_2.12-0.7.1.jar" "$SPLINE_SPARK_AGENT_BUNDLE_URL"
else
    echo "spline-spark-agent-bundle_2.12-0.7.1.jar already exists."
fi

echo "Spline JARs checked/downloaded."


# --- 4. Prepare Configuration and App Files (Placeholders for Demonstration) ---
echo "--- Ensuring application and configuration files are in place ---"
# IMPORTANT: In a real repo, these would be version-controlled, not copied from conceptual_code.
# This assumes the user has already populated these directories as per the HOWTO guide.
# If these files are missing, the docker compose build/run commands might fail.

# FastAPI app files (main.py, requirements.txt, Dockerfile)
# PySpark job files (streaming_consumer.py, batch_transformations.py, etc.)
# Airflow DAGs
# Grafana Alloy config (alloy-config.river)
# OpenMetadata ingestion configs
# Webhook listener app files

# For demonstration, we will create minimal placeholder files if they don't exist
# This ensures `docker compose build` and `up` commands don't fail immediately.
# A user following the HOWTO would have already populated these correctly.
[ -f "./fastapi_app/app/main.py" ] || echo "from fastapi import FastAPI; app = FastAPI(); @app.get('/')\nasync def root(): return {'message': 'Hello'}" > ./fastapi_app/app/main.py
[ -f "./fastapi_app/requirements.txt" ] || echo "fastapi\nuvicorn" > ./fastapi_app/requirements.txt
[ -f "./fastapi_app/Dockerfile" ] || echo "FROM python:3.9-slim-buster\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY app /app/app\nEXPOSE 8000\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]" > ./fastapi_app/Dockerfile

[ -f "./webhook_listener_app/app.py" ] || echo "from flask import Flask, request, jsonify\napp = Flask(__name__)\n@app.route('/health', methods=['GET'])\ndef health_check(): return jsonify({\"status\": \"healthy\"}), 200\n@app.route('/minio-event', methods=['POST'])\ndef minio_event(): print('MinIO event received!'); return jsonify({\"status\": \"success\"})\nif __name__ == '__main__': app.run(host='0.0.0.0', port=8081, debug=True)" > ./webhook_listener_app/app.py
[ -f "./webhook_listener_app/requirements.txt" ] || echo "flask" > ./webhook_listener_app/requirements.txt
[ -f "./webhook_listener_app/Dockerfile" ] || echo "FROM python:3.9-slim-buster\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY app.py .\nEXPOSE 8081\nCMD [\"python\", \"app.py\"]" > ./webhook_listener_app/Dockerfile

[ -f "./observability/alloy-config.river" ] || echo 'prometheus.remote_write "default" { url = "http://grafana:9090/api/prom/push" } otelcol.receiver.otlp "default" { http {} grpc {} output { metrics = [prometheus.remote_write.default.receiver] logs = [otelcol.exporter.logging.log_printer.input] } } otelcol.exporter.logging "log_printer" { log_level = "info" } prometheus.scrape "cadvisor_metrics" { targets = [{"__address__" = "cadvisor:8080"}] forward_to = [prometheus.remote_write.default.receiver] job = "cadvisor" }' > ./observability/alloy-config.river

echo "Placeholder application and configuration files ensured."

# --- 5. Bring up Docker Compose Services ---
echo "--- Bringing up Docker Compose services for the full data platform ---"
echo "This may take a few minutes for all services to start and stabilize."

# Use the comprehensive docker-compose.yml from our previous interaction.
# Assuming this file is present in the current directory.
docker compose up --build -d

# --- 6. Initialize Airflow Database and User ---
echo "--- Initializing Airflow Database and Admin User (first time setup) ---"
echo "Waiting for PostgreSQL and Airflow Webserver to be ready before initializing Airflow DB."

# Wait for PostgreSQL to be healthy
until docker compose ps | grep starter-postgres | grep "healthy"; do
  echo "Waiting for Postgres to be healthy..."
  sleep 5
done

# Wait for airflow-init to complete
echo "Running airflow-init (DB upgrade and user creation)..."
docker compose up airflow-init
# Check if airflow-init completed successfully
if [ $? -ne 0 ]; then
    echo "Error: airflow-init failed. Please check 'docker compose logs airflow-init' for details."
    exit 1
fi
echo "Airflow database initialized and admin user created."

# --- 7. Initialize Kafka Topics ---
echo "--- Initializing Kafka Topics ---"
echo "Waiting for Kafka to be healthy..."
until docker compose ps | grep intermediate-kafka | grep "healthy"; do
  echo "Waiting for Kafka to be healthy..."
  sleep 5
done

# Create raw_financial_transactions topic
docker exec intermediate-kafka kafka-topics --create --topic raw_financial_transactions --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --if-not-exists
# Create raw_insurance_claims topic
docker exec intermediate-kafka kafka-topics --create --topic raw_insurance_claims --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --if-not-exists
# Create a test topic for integration tests if needed, or simply for demonstration
docker exec intermediate-kafka kafka-topics --create --topic raw_data_test --bootstrap-server kafka:29092 --partitions 1 --replication-factor 1 --if-not-exists

echo "Kafka topics created."

# --- 8. Initialize MinIO Buckets and Webhook Configuration ---
echo "--- Initializing MinIO Buckets and Webhook ---"
echo "Waiting for MinIO to be healthy..."
until docker compose ps | grep starter-minio | grep "healthy"; do
  echo "Waiting for MinIO to be healthy..."
  sleep 5
done

echo "Creating MinIO buckets and configuring webhook..."
# Access mc client via the minio container itself
docker exec -it starter-minio /bin/sh -c " \
  mc alias set local http://localhost:9000 minioadmin minioadmin && \
  mc mb local/raw-data-bucket --ignore-existing && \
  mc mb local/curated-data-bucket --ignore-existing && \
  mc mb local/model-output-bucket --ignore-existing && \
  mc mb local/my-event-bucket --ignore-existing && \
  mc event add local/my-event-bucket arn:minio:sqs::1:webhook --suffix .parquet --event put && \
  mc admin config set notify_webhook:webhook_target endpoint='http://webhook_listener:8081/minio-event' queue_limit=100 --console-address \":9001\" \
"

echo "MinIO buckets created and webhook configured. Restarting MinIO for webhook changes to apply..."
docker compose restart minio
echo "MinIO restarted."

# --- 9. Initial MongoDB Data (Optional) ---
echo "--- (Optional) Initializing MongoDB with Sample Data ---"
echo "If MongoDB is critical for your initial setup, you might insert data here."
echo "For now, this is a placeholder. Refer to the HOWTO guide for manual MongoDB data insertion."
echo "Waiting for MongoDB to be healthy..."
until docker compose ps | grep starter-mongodb | grep "healthy"; do
  echo "Waiting for MongoDB to be healthy..."
  sleep 5
done
# Example of inserting data using mongosh if needed:
# docker exec -it starter-mongodb mongosh --authenticationDatabase admin -u root -p password --eval "db.my_data_platform_db.financial_events.insertOne({ 'event_id': 'EVT-001', 'type': 'login_attempt' })"
# This would require careful escaping and data formatting. Manual insertion via shell is often easier for initial setup.

echo "MongoDB initialization check complete."

# --- 10. Final Health Check and UI Access ---
echo "--- Waiting for remaining services to become healthy ---"
# More robust checks for the core UIs
services_to_check=("airflow-webserver" "grafana" "spline-ui" "openmetadata-server" "spark-history-server")
for service in "${services_to_check[@]}"; do
  echo "Waiting for $service UI..."
  attempts=0
  max_attempts=90 # 90 seconds
  # Adjust the URL/port based on the docker-compose-updated-final.yml
  case "$service" in
    "airflow-webserver") HEALTH_URL="http://localhost:8081/health";;
    "grafana") HEALTH_URL="http://localhost:3000/api/health";;
    "spline-ui") HEALTH_URL="http://localhost:9090/";; # Spline UI doesn't have a specific /health API on / endpoint itself
    "openmetadata-server") HEALTH_URL="http://localhost:8585/api/v1/health";;
    "spark-history-server") HEALTH_URL="http://localhost:18080";;
    *) HEALTH_URL="";; # Default to empty for unknown services
  esac

  if [ -n "$HEALTH_URL" ]; then
    until curl -s -f "$HEALTH_URL" >/dev/null; do
      printf "."
      sleep 2
      attempts=$((attempts+1))
      if [ $attempts -ge $max_attempts ]; then
        echo "Error: $service did not become healthy in time. Check 'docker compose logs $service'."
        break
      fi
    done
    if [ $attempts -lt $max_attempts ]; then
      echo "$service UI is healthy."
    fi
  else
    echo "Skipping health check for $service (no specific URL defined)."
  fi
done

echo "--- Environment Setup Complete! ---"
echo "All services should now be running and accessible. Here are the key UIs:"
echo "------------------------------------------------------------------------"
echo "🌐 FastAPI Docs:         http://localhost:8000/docs"
echo "📁 MinIO Console:        http://localhost:9001 (User: minioadmin, Pass: minioadmin)"
echo "🖥️ Spark Master UI:       http://localhost:8088"
echo "📜 Spark History Server: http://localhost:18080"
echo "🚀 Airflow UI:           http://localhost:8081 (User: admin, Pass: admin)"
echo "📊 Grafana UI:           http://localhost:3000 (User: admin, Pass: admin)"
echo "⛓️ Spline UI:            http://localhost:9090"
echo "📚 OpenMetadata UI:      http://localhost:8585"
echo "📈 cAdvisor (raw):       http://localhost:8082"
echo "------------------------------------------------------------------------"
echo "Next Steps:"
echo "1. Generate Data: Run 'python3 simulate_data.py' in a new terminal to send data to FastAPI."
echo "2. Run Spark Streaming: Execute the streaming consumer job via 'docker exec' (see HOWTO for command)."
echo "3. Trigger Airflow DAGs: In Airflow UI, unpause and trigger 'full_pipeline_with_governance' or 'openmetadata_ingestion_dag'."
echo "4. Monitor & Explore: Use Grafana, Spline, and OpenMetadata UIs to observe data flow, metrics, and lineage."
echo ""
echo "To stop all services: 'docker compose down -v'"
echo "------------------------------------------------------------------------"


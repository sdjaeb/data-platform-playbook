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
# Corrected requirements.txt for FastAPI, removing opentelemetry-sdk-metrics and adding correct packages
[ -f "./fastapi_app/requirements.txt" ] || echo "fastapi\nuvicorn\nkafka-python\nopentelemetry-api\nopentelemetry-sdk\nopentelemetry-instrumentation-fastapi\nopentelemetry-exporter-otlp-proto-http" > ./fastapi_app/requirements.txt
[ -f "./fastapi_app/app/main.py" ] || echo "from fastapi import FastAPI; app = FastAPI(); @app.get('/')\nasync def root(): return {'message': 'Hello'}" > ./fastapi_app/app/main.py
[ -f "./fastapi_app/Dockerfile" ] || echo "FROM python:3.9-slim-buster\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY app /app/app\nEXPOSE 8000\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]" > ./fastapi_app/Dockerfile

[ -f "./webhook_listener_app/app.py" ] || echo "from flask import Flask, request, jsonify\napp = Flask(__name__)\n@app.route('/health', methods=['GET'])\ndef health_check(): return jsonify({\"status\": \"healthy\"}), 200\n@app.route('/minio-event', methods=['POST'])\ndef minio_event(): print('MinIO event received!'); return jsonify({\"status\": \"success\"})\nif __name__ == '__main__': app.run(host='0.0.0.0', port=8081, debug=True)" > ./webhook_listener_app/app.py
[ -f "./webhook_listener_app/requirements.txt" ] || echo "flask" > ./webhook_listener_app/requirements.txt
[ -f "./webhook_listener_app/Dockerfile" ] || echo "FROM python:3.9-slim-buster\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY app.py .\nEXPOSE 8081\nCMD [\"python\", \"app.py\"]" > ./webhook_listener_app/Dockerfile

# Updated alloy-config.river with proper newlines
# if [ ! -f "./observability/alloy-config.river" ]; then
#   cat <<EOF > "./observability/alloy-config.river"
# prometheus.remote_write "default" {
#   url = "http://grafana:9090/api/prom/push"
# }

# otelcol.receiver.otlp "default" {
#   http {}
#   grpc {}
#   output {
#     metrics = [prometheus.remote_write.default.receiver]
#     logs = [otelcol.exporter.logging.log_printer.input]
#   }
# }

# otelcol.exporter.logging "log_printer" {
#   log_level = "info"
# }

# prometheus.scrape "cadvisor_metrics" {
#   targets = [{"__address__" = "cadvisor:8080"}]
#   forward_to = [prometheus.remote_write.default.receiver]
#   job = "cadvisor"
# }
# EOF
# fi

# Placeholder for data_arrival_sensor_dag.py
# This provides a minimal working DAG that matches the "Next Steps" instructions.
# It allows the user to trigger the main pipeline successfully on first run.
if [ ! -f "./airflow_dags/full_pipeline_with_governance.py" ]; then
  cat <<EOF > "./airflow_dags/full_pipeline_with_governance.py"
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id='full_pipeline_with_governance',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['example', 'data-platform'],
    doc_md="""
    ### Full Pipeline with Governance DAG

    This is a placeholder DAG for the main data pipeline.
    In a real scenario, this would trigger Spark jobs for transformation
    and OpenMetadata ingestion for lineage.
    """,
) as dag:
    start_pipeline = BashOperator(
        task_id='start_pipeline',
        bash_command='echo "Starting the full data pipeline... (This is a placeholder)"',
    )
EOF
fi

echo "Placeholder application and configuration files ensured."

# --- 5. Bring up Docker Compose Services ---
echo "--- Bringing up Docker Compose services for the full data platform ---"
echo "This will wait for all services to become healthy and may take several minutes."
echo "Note: The platform is defined across multiple 'docker-compose.*.yml' files."
echo "The main 'docker-compose.yml' uses the 'include' directive to combine them."
echo "This allows for a modular setup."


# The '--wait' flag tells Compose to wait until all services with a healthcheck
# are in a 'healthy' state. This simplifies the script by removing manual polling loops.
# It also ensures that one-off initialization containers (like airflow-init) have
# completed successfully, as other services depend on them.
docker compose up --build -d --wait

echo "All services are up and healthy."

# --- 6. Confirm Airflow Initialization ---
echo "--- Airflow initialization is handled by docker-compose dependencies. Verifying... ---"
if [ "$(docker compose ps -q --status=exited airflow-init | wc -l)" -eq 0 ]; then
    echo "Warning: airflow-init did not complete as expected. Manual check may be required."
else
    echo "Airflow database and user initialized successfully."
fi

# --- 7. Initialize Kafka Topics ---
echo "--- Initializing Kafka Topics (services are healthy) ---"
# Create raw_financial_transactions topic
docker exec kafka kafka-topics --create --topic raw_financial_transactions --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --if-not-exists
# Create raw_insurance_claims topic
docker exec kafka kafka-topics --create --topic raw_insurance_claims --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --if-not-exists
# Create a test topic for integration tests if needed, or simply for demonstration
docker exec kafka kafka-topics --create --topic raw_data_test --bootstrap-server kafka:29092 --partitions 1 --replication-factor 1 --if-not-exists
echo "Kafka topics created."

# --- 8. Initialize MinIO Buckets and Webhook Configuration ---
echo "--- Initializing MinIO Buckets and Webhook (services are healthy) ---"
# Access mc client via the minio container itself
# Removed -it flags as they are not suitable for non-interactive scripts
docker exec minio /bin/sh -c " \
  mc alias set local http://localhost:9000 minioadmin minioadmin && \
  mc mb local/raw-data-bucket --ignore-existing && \
  mc mb local/curated-data-bucket --ignore-existing && \
  mc mb local/model-output-bucket --ignore-existing && \
  mc mb local/my-event-bucket --ignore-existing && \
  mc admin config set local notify_webhook:1 endpoint='http://webhook-listener:8081/minio-event' queue_limit='100' && \
  mc event add local/my-event-bucket arn:minio:sqs::1:webhook --suffix .parquet --event put \
"

echo "MinIO buckets created and webhook configured. Restarting MinIO for webhook changes to apply..."
docker compose restart minio
echo "MinIO restarted."

# --- 9. Initial MongoDB Data (Optional) ---
echo "--- (Optional) Initializing MongoDB with Sample Data ---"
echo "If MongoDB is critical for your initial setup, you might insert data here."
echo "For now, this is a placeholder. 'docker compose up --wait' ensures MongoDB is healthy."
# Example of inserting data using mongosh if needed:
# docker exec -it mongodb mongosh --authenticationDatabase admin -u root -p password --eval "db.my_data_platform_db.financial_events.insertOne({ 'event_id': 'EVT-001', 'type': 'login_attempt' })"
# This would require careful escaping and data formatting. Manual insertion via shell is often easier for initial setup.

echo "MongoDB initialization check complete."

# --- 10. Final Health Check and UI Access ---
echo "--- Waiting for remaining services to become healthy ---"
# This final check is kept for user experience, providing a clear confirmation that UIs are accessible.
# The 'docker compose up --wait' command should have already ensured services are healthy.
# More robust checks for the core UIs
services_to_check=("airflow-webserver" "grafana" "spline-ui" "openmetadata-server" "spark-history-server" "superset")
for service in "${services_to_check[@]}"; do
  echo "Waiting for $service UI..."
  attempts=0
  max_attempts=90 # 90 seconds
  # Adjust the URL/port based on the docker-compose.yml
  case "$service" in
    "superset") HEALTH_URL="http://localhost:8088/health";;
    "airflow-webserver") HEALTH_URL="http://localhost:8080/health";;
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
echo "🖥️ Spark Master UI:       http://localhost:8081"
echo "📜 Spark History Server: http://localhost:18080"
echo "🚀 Airflow UI:           http://localhost:8080 (User: admin, Pass: admin)"
echo "📊 Grafana UI:           http://localhost:3000 (User: admin, Pass: admin)"
echo "⛓️ Spline UI:            http://localhost:9090"
echo "📚 OpenMetadata UI:      http://localhost:8585 (User: admin, Pass: admin)"
echo "🎨 Superset UI:          http://localhost:8088 (User: admin, Pass: admin)"
echo "📈 cAdvisor (raw):       http://localhost:8083"
echo "------------------------------------------------------------------------"
echo "Next Steps:"
echo "1. Generate Data: Run 'python3 simulate_data.py' in a new terminal to send data to FastAPI."
echo "2. Run Spark Streaming: Execute the streaming consumer job via 'docker exec' (see HOWTO for command)."
echo "3. Trigger Airflow DAGs: In Airflow UI, unpause and trigger 'full_pipeline_with_governance' or 'openmetadata_ingestion_dag'."
echo "4. Monitor & Explore: Use Grafana, Spline, and OpenMetadata UIs to observe data flow, metrics, and lineage."
echo ""
echo "To stop all services: 'docker compose down -v'"
echo "------------------------------------------------------------------------"

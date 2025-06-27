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
  echo "Warning: Locust (for load testing) is not installed. You can install it later with 'python3 -m pip install locust'."
fi

echo "All essential prerequisites appear to be met."

# --- 2. Project Directory Setup ---
echo "--- Setting up project directories ---"
mkdir -p data/{postgres,mongodb,minio,spark-events,grafana,airflow_logs,openmetadata_elasticsearch,spline_jars}
mkdir -p fastapi_app/app
mkdir -p pyspark_jobs
mkdir -p airflow_dags
mkdir -p observability/{grafana_dashboards}
touch platform-core/observability/grafana_datasources.yml
mkdir -p openmetadata_ingestion_scripts
mkdir -p webhook_listener_app
mkdir -p dbt_projects
mkdir -p dbt_profiles

# Create directories for data generators at the repo root
mkdir -p ../data-generators/financial-generator
mkdir -p ../data-generators/insurance-generator
mkdir -p ../data-generators/sports-generator

# Create dummy files/directories if they don't exist, as required by docker-compose mounts
touch ./observability/alloy-config.river # Ensure this file exists for Grafana Alloy mount
# Corrected requirements.txt for FastAPI, removing opentelemetry-sdk-metrics and adding correct packages
[ -f "./fastapi_app/requirements.txt" ] || echo "fastapi\nuvicorn\nkafka-python\nopentelemetry-api\nopentelemetry-sdk\nopentelemetry-instrumentation-fastapi\nopentelemetry-exporter-otlp-proto-http" > ./fastapi_app/requirements.txt
[ -f "./fastapi_app/app/main.py" ] || echo "from fastapi import FastAPI; app = FastAPI(); @app.get('/')\nasync def root(): return {'message': 'Hello'}" > ./fastapi_app/app/main.py
[ -f "./fastapi_app/Dockerfile" ] || echo "FROM python:3.9-slim-buster\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY app /app/app\nEXPOSE 8000\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]" > ./fastapi_app/Dockerfile

[ -f "./webhook_listener_app/app.py" ] || echo "from flask import Flask, request, jsonify\napp = Flask(__name__)\n@app.route('/health', methods=['GET'])\ndef health_check(): return jsonify({\"status\": \"healthy\"}), 200\n@app.route('/minio-event', methods=['POST'])\ndef minio_event(): print('MinIO event received!'); return jsonify({\"status\": \"success\"})\nif __name__ == '__main__': app.run(host='0.0.0.0', port=8081, debug=True)" > ./webhook_listener_app/app.py
[ -f "./webhook_listener_app/requirements.txt" ] || echo "flask" > ./webhook_listener_app/requirements.txt
[ -f "./webhook_listener_app/Dockerfile" ] || echo "FROM python:3.9-slim-buster\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY app.py .\nEXPOSE 8081\nCMD [\"python\", \"app.py\"]" > ./webhook_listener_app/Dockerfile

# Placeholder for the main pipeline DAG.
# This provides a minimal working DAG that matches the "Next Steps" instructions.
# It allows the user to trigger the main pipeline successfully on first run.
if [ ! -f "./airflow_dags/full_pipeline_with_governance_dag.py" ]; then
  cat <<EOF > "./airflow_dags/full_pipeline_with_governance_dag.py"
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

# Create placeholder dbt profiles.yml if it doesn't exist
if [ ! -f "./dbt_profiles/profiles.yml" ]; then
  cat <<EOF > "./dbt_profiles/profiles.yml"
data_platform_project:
  target: dev
  outputs:
    dev:
      type: spark
      method: thrift
      host: "{{ env_var('DBT_SPARK_HOST') }}"
      port: "{{ env_var('DBT_SPARK_PORT') | int }}"
      schema: "{{ env_var('DBT_SPARK_SCHEMA') }}"
      catalog: "{{ env_var('DBT_SPARK_CATALOG') }}"
      connect_options:
        spark.hadoop.fs.s3a.endpoint: "{{ env_var('DBT_SPARK_S3_ENDPOINT') }}"
        spark.hadoop.fs.s3a.access.key: "{{ env_var('DBT_SPARK_AWS_ACCESS_KEY_ID') }}"
        spark.hadoop.fs.s3a.secret.key: "{{ env_var('DBT_SPARK_AWS_SECRET_ACCESS_KEY') }}"
        spark.hadoop.fs.s3a.path.style.access: "true"
        spark.hadoop.fs.s3a.impl: "org.apache.hadoop.fs.s3a.S3AFileSystem"
        spark.hadoop.fs.s3a.connection.ssl.enabled: "false"
        spark.sql.extensions: "io.delta.sql.DeltaSparkSessionExtension"
        spark.sql.catalog.spark_catalog: "org.apache.spark.sql.delta.catalog.DeltaCatalog"
      meta_host: "{{ env_var('DBT_PG_HOST') }}"
      meta_port: "{{ env_var('DBT_PG_PORT') | int }}"
      meta_user: "{{ env_var('DBT_PG_USER') }}"
      meta_password: "{{ env_var('DBT_PG_PASSWORD') }}"
      meta_dbname: "{{ env_var('DBT_PG_DBNAME') }}"
EOF
fi

################################################################################
# Create placeholder files for data generators
################################################################################

DOCKERFILE_CONTENT=$(cat <<'EOF'
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .

# Use pip to install packages
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
CMD ["python", "main.py"]
EOF
)

for generator in financial-generator insurance-generator sports-generator; do
  echo "$DOCKERFILE_CONTENT" > "../data-generators/$generator/Dockerfile"
  echo -e "requests\nFaker\nflask\nkafka-python" > "../data-generators/$generator/requirements.txt"
  cat > "../data-generators/$generator/main.py" <<PYEOF
import threading
import time
import random
import os
import json
from datetime import datetime
from flask import Flask
from kafka import KafkaProducer
from faker import Faker

fake = Faker()
app = Flask(__name__)
running = False
producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BROKER", "kafka:29092"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

GENERATOR = "${generator}"

if GENERATOR == "financial-generator":
    TOPIC_RAW = "raw_financial_events"
    TOPIC_MALFORMED = "malformed_financial_events"
    def generate_valid():
        return {
            "transaction_id": f"FT-{random.randint(1000,9999)}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "account_id": f"ACC-{random.randint(100,999)}",
            "amount": round(random.uniform(10, 1000), 2),
            "currency": random.choice(["USD", "EUR", "GBP"]),
            "transaction_type": random.choice(["debit", "credit"]),
            "merchant_id": f"MER-{fake.lexify(text='???')}",
            "category": random.choice(["groceries", "electronics", "travel"])
        }
elif GENERATOR == "insurance-generator":
    TOPIC_RAW = "raw_insurance_claims"
    TOPIC_MALFORMED = "malformed_insurance_claims"
    def generate_valid():
        return {
            "claim_id": f"IC-{random.randint(1000,9999)}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "policy_number": f"POL-{random.randint(100000,999999)}",
            "claim_amount": round(random.uniform(100, 10000), 2),
            "claim_type": random.choice(["auto", "home", "health"]),
            "claim_status": random.choice(["submitted", "approved", "rejected"]),
            "customer_id": f"CUST-{fake.lexify(text='???')}",
            "incident_date": datetime.utcnow().isoformat() + "Z"
        }
elif GENERATOR == "sports-generator":
    TOPIC_RAW = "raw_sports_events"
    TOPIC_MALFORMED = "malformed_sports_events"
    def generate_valid():
        return {
            "event_id": f"SE-{random.randint(1000,9999)}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sport": random.choice(["soccer", "basketball", "tennis"]),
            "team_a": fake.company(),
            "team_b": fake.company(),
            "score_a": random.randint(0, 5),
            "score_b": random.randint(0, 5),
            "location": fake.city(),
            "status": random.choice(["scheduled", "in_progress", "finished"])
        }
else:
    raise Exception("Unknown generator type")

def generate_data():
    global running
    while running:
        msg = generate_valid()
        producer.send(TOPIC_RAW, msg)
        print(f"Sent: {msg}")
        time.sleep(1)

@app.route('/start')
def start():
    global running
    if not running:
        running = True
        threading.Thread(target=generate_data, daemon=True).start()
    return "Started"

@app.route('/stop')
def stop():
    global running
    running = False
    return "Stopped"

@app.route('/malformed')
def malformed():
    count = random.randint(1, 10)
    for _ in range(count):
        bad_msg = {"bad_field": "malformed_data", "timestamp": datetime.utcnow().isoformat() + "Z"}
        producer.send(TOPIC_MALFORMED, bad_msg)
        print(f"Sent malformed: {bad_msg}")
    return f"Sent {count} malformed messages"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
PYEOF
done

echo "Placeholder application and configuration files ensured."

# --- 5. Bring up Docker Compose Services ---
echo "--- Bringing up Docker Compose services for the full data platform ---"
echo "This will wait for all services to become healthy and may take several minutes."
echo "Note: The platform is defined across multiple 'docker-compose.*.yml' files."
echo "The main 'docker-compose.yml' uses the 'include' directive to combine them."
echo "This allows for a modular setup."

# The '--wait' flag is a crucial part of this command. It instructs Docker Compose
# to wait until all services that have a `healthcheck` defined in their
# respective docker-compose.*.yml file are in a 'healthy' state before proceeding.
# This eliminates the need for manual `sleep` commands or polling loops in this script.
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

# Financial
docker exec kafka kafka-topics --create --topic raw_financial_events --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --config retention.ms=86400000 --if-not-exists
docker exec kafka kafka-topics --create --topic malformed_financial_events --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --config retention.ms=86400000 --if-not-exists
docker exec kafka kafka-topics --create --topic curated_financial_events --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --config retention.ms=604800000 --if-not-exists
docker exec kafka kafka-topics --create --topic dlq_financial_events --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --config retention.ms=604800000 --if-not-exists

# Insurance
docker exec kafka kafka-topics --create --topic raw_insurance_claims --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --config retention.ms=86400000 --if-not-exists
docker exec kafka kafka-topics --create --topic malformed_insurance_claims --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --config retention.ms=86400000 --if-not-exists
docker exec kafka kafka-topics --create --topic curated_insurance_claims --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --config retention.ms=604800000 --if-not-exists
docker exec kafka kafka-topics --create --topic dlq_insurance_claims --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --config retention.ms=604800000 --if-not-exists

# Sports
docker exec kafka kafka-topics --create --topic raw_sports_events --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --config retention.ms=86400000 --if-not-exists
docker exec kafka kafka-topics --create --topic malformed_sports_events --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --config retention.ms=86400000 --if-not-exists
docker exec kafka kafka-topics --create --topic curated_sports_events --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --config retention.ms=604800000 --if-not-exists
docker exec kafka kafka-topics --create --topic dlq_sports_events --bootstrap-server kafka:29092 --partitions 3 --replication-factor 1 --config retention.ms=604800000 --if-not-exists

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

# --- 9. Verify dbt connection ---
echo "--- Verifying dbt connection to Spark and Postgres ---"
docker compose exec dbt dbt debug --profiles-dir /usr/app/dbt_profiles
echo "dbt debug command executed. Check output for successful connection."

# --- 9. Initial MongoDB Data (Optional) ---
echo "--- (Optional) Initializing MongoDB with Sample Data ---"
echo "If MongoDB is critical for your initial setup, you might insert data here."
echo "For now, this is a placeholder. 'docker compose up --wait' ensures MongoDB is healthy."
# Example of inserting data using mongosh if needed:
# docker exec -it mongodb mongosh --authenticationDatabase admin -u root -p password --eval "db.my_data_platform_db.financial_events.insertOne({ 'event_id': 'EVT-001', 'type': 'login_attempt' })"
# This would require careful escaping and data formatting. Manual insertion via shell is often easier for initial setup.

echo "MongoDB initialization check complete."

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
echo "🛠️ dbt CLI:              Run commands via 'docker compose exec dbt dbt <command>'"
echo "🎨 Superset UI:          http://localhost:8088 (User: admin, Pass: admin)"
echo "📈 cAdvisor (raw):       http://localhost:8083"
echo "------------------------------------------------------------------------"
echo "Next Steps:"
echo "1. Start Sending Data: Use `curl` to start one or more data generators from a new terminal."
echo "   - Financial Data: curl http://localhost:5001/start"
echo "   - Insurance Data: curl http://localhost:5002/start"
echo "   - Sports Data:    curl http://localhost:5003/start"
echo ""
echo "2. Review Data Flow & Process Data:"
echo "   - For detailed CLI commands to verify data flow in Kafka, MinIO, MongoDB, and PostgreSQL, see:"
echo "     `./docs/data_flow_verification_cheatsheet.md`"
echo "   - Observe data in Kafka topics (e.g., using 'kcat')."
echo "   - Run Spark jobs to process streaming data into MinIO's 'raw-data-bucket' (see docs for commands)."
echo "   - In Airflow (http://localhost:8080), unpause and trigger 'full_pipeline_with_governance' to run batch transformations."
echo "   - Explore lineage in Spline (http://localhost:9090) and metadata in OpenMetadata (http://localhost:8585)."
echo ""
echo "3. Stop Sending Data: When you're done, stop the generators."
echo "   - Financial Data: curl http://localhost:5001/stop"
echo "   - Insurance Data: curl http://localhost:5002/stop"
echo "   - Sports Data:    curl http://localhost:5003/stop"
echo ""
echo "To stop all services: 'docker compose down -v'"
echo "------------------------------------------------------------------------"

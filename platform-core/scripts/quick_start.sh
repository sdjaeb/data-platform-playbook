# Description: Bootstrap script for local data platform environment.
# Source: Building Enterprise-Ready Data Platforms v2.4, Section 8.1.
#
# This script is a conceptual quick-start to bring up the entire local environment.
# It assumes conceptual code examples are located in 'conceptual_code/'
# relative to where this quick_start.sh script is placed.
#!/bin/bash

# quick_start.sh - Bootstrap script for local data platform environment

# --- Prerequisites Check ---
echo "--- Checking Prerequisites ---"
command -v docker >/dev/null 2>&1 || { echo >&2 "Docker is required but not installed. Aborting."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo >&2 "Docker Compose is required but not installed. Aborting."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo >&2 "Python3 is required but not installed. Aborting."; exit 1; }
# command -v uv >/dev/null 2>&1 || { echo >&2 "uv (pip install uv) is recommended but not installed. Proceeding anyway."; } # Commented out as uv might not be universally installed
command -v sam >/dev/null 2>&1 || { echo >&2 "AWS SAM CLI is required but not installed. Aborting."; exit 1; }
echo "All prerequisites appear to be met."

# --- Project Setup ---
echo "--- Setting up project directories ---"
mkdir -p data/{postgres,mongodb,minio,spark-events,grafana,airflow_logs,openmetadata_mysql,openmetadata_elasticsearch}
mkdir -p src/{common,models} # Simplified, as per consolidated structure
mkdir -p fastapi_app/{app,tests/unit,tests/integration}
mkdir -p pyspark_jobs/{tests/unit,tests/contract}
mkdir -p airflow_dags
mkdir -p terraform_infra/{modules/{s3_data_lake,msk_kafka,rds_postgres,lambda_api_ingestor},environments/{dev,staging,prod}} # Added lambda_api_ingestor
mkdir -p observability/{dashboards,grafana_dashboards_provisioning,grafana_datasources_provisioning}
mkdir -p openmetadata_ingestion_scripts
mkdir -p runbooks
mkdir -p load_testing # For locust script
mkdir -p sam_lambda/hello_world/highlights # For SAM lambda app.py files
echo "Project directories created."

echo "--- Copying conceptual code snippets to working directories ---"
# Copy FastAPI app code for each track from conceptual_code/fastapi_app/app/highlights
cp conceptual_code/fastapi_app/app/highlights/main_starter.py ./fastapi_app/app/main_starter.py
cp conceptual_code/fastapi_app/app/highlights/main_intermediate.py ./fastapi_app/app/main_intermediate.py
cp conceptual_code/fastapi_app/app/highlights/main_advanced.py ./fastapi_app/app/main.py # Use advanced as main.py for full setup
cp conceptual_code/fastapi_app/Dockerfile ./fastapi_app/Dockerfile
cp conceptual_code/fastapi_app/requirements.txt ./fastapi_app/requirements.txt
cp conceptual_code/fastapi_app/app/tests/unit/highlights/test_api.py ./fastapi_app/tests/unit/test_api.py
cp conceptual_code/fastapi_app/app/tests/integration/highlights/test_data_flow.py ./fastapi_app/tests/integration/test_data_flow.py

# Copy PySpark jobs
cp conceptual_code/pyspark_jobs/highlights/streaming_consumer.py ./pyspark_jobs/streaming_consumer.py
cp conceptual_code/pyspark_jobs/highlights/batch_transformations.py ./pyspark_jobs/batch_transformations.py
cp conceptual_code/pyspark_jobs/highlights/mongo_processor.py ./pyspark_jobs/mongo_processor.py
cp conceptual_code/pyspark_jobs/highlights/streaming_consumer_test.py ./pyspark_jobs/streaming_consumer_test.py
cp conceptual_code/pyspark_jobs/tests/contract/highlights/financial_transaction_consumer_pact.py ./pyspark_jobs/tests/contract/financial_transaction_consumer_pact.py


# Copy Airflow DAGs
cp conceptual_code/airflow_dags/highlights/simple_etl_dag.py ./airflow_dags/simple_etl_dag.py
cp conceptual_code/airflow_dags/highlights/spark_data_pipeline_dag.py ./airflow_dags/spark_data_pipeline_dag.py
cp conceptual_code/airflow_dags/highlights/simple_etl_workflow_with_failure.py ./airflow_dags/simple_etl_workflow_with_failure.py
cp conceptual_code/airflow_dags/highlights/data_producer_dag.py ./airflow_dags/data_producer_dag.py
cp conceptual_code/airflow_dags/highlights/data_consumer_dag.py ./airflow_dags/data_consumer_dag.py
cp conceptual_code/airflow_dags/highlights/data_arrival_sensor_dag.py ./airflow_dags/data_arrival_sensor_dag.py

# Copy Observability config
cp conceptual_code/observability/highlights/alloy-config.river ./observability/alloy-config.river
# cp conceptual_code/observability/dashboards/health_dashboard.json ./observability/dashboards/health_dashboard.json # Placeholder

# Copy sample runbooks (if any conceptual ones were provided)
# cp conceptual_code/runbooks/* ./runbooks/ # Assuming this will be filled in later

# Copy Terraform module for Lambda API Ingestor
mkdir -p terraform_infra/modules/lambda_api_ingestor
cp conceptual_code/terraform_infra/modules/lambda_api_ingestor/highlights/main.tf ./terraform_infra/modules/lambda_api_ingestor/main.tf

# Copy SAM Lambda app code
mkdir -p sam_lambda/hello_world
cp conceptual_code/sam_lambda/hello_world/highlights/app_basic.py ./sam_lambda/hello_world/app.py # Set basic as default
cp conceptual_code/sam_lambda/hello_world/highlights/app_localstack_s3.py ./sam_lambda/hello_world/app_localstack_s3.py
# Create dummy requirements.txt for SAM lambda
echo "boto3" > ./sam_lambda/hello_world/requirements.txt
# Create dummy template.yaml for SAM lambda (user needs to fill out resources)
echo "AWSTemplateFormatVersion: '2010-09-09'\nTransform: AWS::Serverless-2016-10-31\nDescription: A simple SAM lambda for testing.\nResources:\n  HelloWorldFunction:\n    Type: AWS::Serverless::Function\n    Properties:\n      Handler: app.lambda_handler\n      Runtime: python3.9\n      Architectures:\n        - x86_64\n      Events:\n        HelloWorld: # API Gateway endpoint\n          Type: Api\n          Properties:\n            Path: /hello\n            Method: get\n" > ./sam_lambda/template.yaml


# Copy Locust load test script
cp conceptual_code/load_testing/highlights/locust_fastapi_ingestor.py ./load_testing/locust_fastapi_ingestor.py


# Copy master docker-compose.yml (assuming it combines all tracks as in Appendix E)
# For this exercise, we will use the content from docker-compose-advanced.yml
cp conceptual_code/docker_compose/highlights/docker-compose-advanced.yml ./docker-compose.yml
cp conceptual_code/docker_compose/docker-compose.test.yml ./docker-compose.test.yml

echo "Conceptual code snippets copied."

# --- Docker Compose Setup ---
echo "--- Bringing up Docker Compose services (Advanced Track) ---"
echo "This may take a few minutes for all services to start and stabilize."
# Note: The original quick_start.sh listed all services. For brevity here,
# and assuming docker-compose.yml is the full advanced track, we just use that.
docker compose -f docker-compose.yml up --build -d \
zookeeper kafka minio cadvisor \
fastapi_ingestor \
postgres mongodb \
spark-master spark-worker-1 spark-worker-2 spark-history-server \
airflow-webserver airflow-scheduler \
grafana grafana_alloy \
spline-rest spline-ui \
openmetadata-mysql openmetadata-elasticsearch openmetadata-server

# --- Initialize Airflow Database ---
echo "--- Initializing Airflow Database (first time setup) ---"
# Give postgres some time to fully initialize
sleep 20
# For Airflow 2.x, init is typically done via a separate container or init command.
# Assuming an 'airflow-init' service is defined in docker-compose.yml or run separately.
# If 'airflow-init' service exists (as in main docs, Advanced Track), run it.
docker compose up airflow-init || echo "airflow-init service might not be defined or already run successfully."

echo "Airflow database initialization started. Check logs if it fails."

echo "--- Waiting for services to become healthy (this may take a few more minutes) ---"
# Simple loop to wait for key services. For production, use better health checks.
services_to_check=("fastapi_ingestor" "kafka" "spark-master" "airflow-webserver" "grafana" "openmetadata-server")
for service in "${services_to_check[@]}"; do
  echo "Waiting for $service..."
  # Use a more robust health check loop
  attempts=0
  max_attempts=60 # 60 seconds
  until docker compose ps --filter "name=${service}" --filter "status=running" --filter "health=healthy" | grep -q "${service}"; do
    printf "."
    sleep 1
    attempts=$((attempts+1))
    if [ $attempts -ge $max_attempts ]; then
      echo "$service did not become healthy in time. Check logs."
      break
    fi
  done
  if [ $attempts -lt $max_attempts ]; then
    echo "$service is healthy."
  fi
done

echo "--- Environment Setup Complete! ---"
echo "You can now access the following UIs:"
echo " MinIO Console: http://localhost:9901 (User: minioadmin, Pass: minioadmin)"
echo " FastAPI Docs: http://localhost:8000/docs"
echo " Spark Master UI: http://localhost:8080"
echo " Airflow UI: http://localhost:8081 (if mapped like this in compose, else check your config)"
echo " Grafana UI: http://localhost:3000 (User: admin, Pass: admin)"
echo " Spline UI: http://localhost:9090 (if mapped like this in compose, else check your config)"
echo " OpenMetadata UI: http://localhost:8585"
#!/bin/bash

# create_project_directories.sh
# This script creates the directory structure for the Enterprise-Ready Data Platform project.

echo "Creating project directory structure..."

# Base directory
mkdir -p platform-core 

# Navigate into the base directory to create subdirectories relative to it
cd platform-core || { echo "Failed to navigate to platform-core"; exit 1; }

# Top-level directories
mkdir -p .github/workflows
mkdir -p data/{postgres,mongodb,minio,spark-events,grafana,airflow_logs,openmetadata_mysql,openmetadata_elasticsearch}
mkdir -p src/{common,models}
mkdir -p fastapi_app/{app,tests/{unit,integration}}
mkdir -p pyspark_jobs/{tests/{unit,contract}}
mkdir -p airflow_dags
mkdir -p observability
mkdir -p openmetadata_ingestion_scripts
mkdir -p terraform_infra/{modules/{s3_data_lake,msk_kafka,rds_postgres,lambda_api_ingestor},environments/{dev,staging,prod}}
mkdir -p sam_lambda/hello_world
mkdir -p load_testing
mkdir -p scripts
mkdir -p conceptual_code

echo "Directory structure created successfully."

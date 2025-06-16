# airflow_dags/openmetadata_ingestion_dag.py
# This Airflow DAG is responsible for orchestrating the ingestion of metadata
# from various data sources (Kafka, MinIO/S3, PostgreSQL, Spark/Spline, FastAPI, MongoDB)
# into OpenMetadata. It uses BashOperators to run Python scripts
# which leverage the OpenMetadata Python client for ingestion.

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator # For start/end tasks
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='openmetadata_ingestion_dag',
    default_args=default_args,
    description='DAG to ingest metadata into OpenMetadata from various sources.',
    schedule_interval=timedelta(hours=1), # Run hourly, or daily, or on a specific schedule
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['openmetadata', 'governance', 'metadata'],
) as dag:

    start_ingestion = DummyOperator(task_id='start_metadata_ingestion')

    # IMPORTANT NOTE: These BashOperators assume that the `openmetadata-ingestion`
    # container is accessible from the Airflow worker, and that the Python client
    # is installed within the `openmetadata-ingestion` image.
    # The `bash_command` paths refer to the files mounted in the
    # `openmetadata-ingestion` service's `/opt/openmetadata/examples/workflows` volume.

    # Task to ingest metadata from Kafka topics
    ingest_kafka_metadata = BashOperator(
        task_id='ingest_kafka_metadata',
        bash_command='docker exec advanced-openmetadata-ingestion python '
                     '/opt/openmetadata/examples/workflows/run_metadata_workflow.py '
                     '--config /opt/openmetadata/examples/workflows/kafka_connector_config.yaml',
    )

    # Task to ingest metadata from MinIO (S3-compatible) Delta Lake tables
    ingest_minio_s3_metadata = BashOperator(
        task_id='ingest_minio_s3_metadata',
        bash_command='docker exec advanced-openmetadata-ingestion python '
                     '/opt/openmetadata/examples/workflows/run_metadata_workflow.py '
                     '--config /opt/openmetadata/examples/workflows/s3_delta_connector_config.yaml',
    )

    # Task to ingest metadata from PostgreSQL database (e.g., application metadata, Airflow metastore)
    ingest_postgres_metadata = BashOperator(
        task_id='ingest_postgres_metadata',
        bash_command='docker exec advanced-openmetadata-ingestion python '
                     '/opt/openmetadata/examples/workflows/run_metadata_workflow.py '
                     '--config /opt/openmetadata/examples/workflows/postgres_connector_config.yaml',
    )

    # Task to ingest lineage from Spline (Spark lineage)
    # IMPORTANT NOTE: This task should run after Spark jobs have executed and generated
    # lineage in the Spline backend.
    ingest_spline_lineage = BashOperator(
        task_id='ingest_spline_lineage',
        bash_command='docker exec advanced-openmetadata-ingestion python '
                     '/opt/openmetadata/examples/workflows/run_metadata_workflow.py '
                     '--config /opt/openmetadata/examples/workflows/spline_connector_config.yaml',
    )

    # Task to ingest metadata from FastAPI (API endpoints)
    ingest_fastapi_metadata = BashOperator(
        task_id='ingest_fastapi_metadata',
        bash_command='docker exec advanced-openmetadata-ingestion python '
                     '/opt/openmetadata/examples/workflows/run_metadata_workflow.py '
                     '--config /opt/openmetadata/examples/workflows/fastapi_connector_config.yaml',
    )

    # Task to ingest metadata from MongoDB
    ingest_mongodb_metadata = BashOperator(
        task_id='ingest_mongodb_metadata',
        bash_command='docker exec advanced-openmetadata-ingestion python '
                     '/opt/openmetadata/examples/workflows/run_metadata_workflow.py '
                     '--config /opt/openmetadata/examples/workflows/mongodb_connector_config.yaml',
    )

    end_ingestion = DummyOperator(task_id='end_metadata_ingestion')

    # Define the task dependencies
    start_ingestion >> [
        ingest_kafka_metadata,
        ingest_minio_s3_metadata,
        ingest_postgres_metadata,
        ingest_spline_lineage,
        ingest_fastapi_metadata,
        ingest_mongodb_metadata
    ] >> end_ingestion


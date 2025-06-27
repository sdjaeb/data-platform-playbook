# airflow_dags/full_pipeline_with_governance_dag.py
# This Airflow DAG orchestrates a full end-to-end data pipeline,
# from simulated data ingestion through Spark transformations,
# data validation, and finally, metadata ingestion into OpenMetadata.
# It demonstrates how Airflow can manage complex workflows across
# different data platform components.

from airflow import DAG
from airflow.operators.bash import BashOperator # Keep BashOperator for spark-submit
from airflow.operators.empty import EmptyOperator # Replaced DummyOperator
from datetime import datetime, timedelta # Use datetime for start_date

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='full_pipeline_with_governance',
    default_args=default_args,
    description='End-to-end data pipeline for financial data with governance integration.',
    schedule_interval=timedelta(days=1), # Run daily
    start_date=days_ago(1),
    catchup=False,
    tags=['etl', 'spark', 'governance', 'openmetadata'],
) as dag:

    # 1. Start Ingestion (Conceptual / Trigger point)
    start_ingestion = EmptyOperator(
        task_id='start_data_ingestion',
        doc_md="""
        ### Start Data Ingestion
        This task conceptually represents the start of data ingestion,
        e.g., through FastAPI receiving data. For this DAG, it's a dummy
        task, as the `simulate_data.py` runs continuously.
        """,
    )

    # 2. Run Spark Streaming Consumer (Continuous, for demo, typically external to batch DAG)
    # IMPORTANT NOTE: This task is conceptual for a batch DAG. In a real streaming scenario,
    # the Spark streaming consumer (`streaming_consumer.py`) would be a long-running application
    # external to the daily batch DAG, continuously writing to the raw Delta table.
    # For demonstration purposes, we assume the raw data is already present from the streaming job.
    prepare_raw_data_delta = EmptyOperator(
        task_id='prepare_raw_data_in_delta_lake',
        doc_md="""
        ### Prepare Raw Data in Delta Lake
        This task conceptually represents the continuous streaming ingestion
        of raw financial data from Kafka to MinIO (Delta Lake) by a Spark Structured Streaming job.
        For this batch DAG, we assume the raw data is already present and ready for transformation.
        """,
    )

    # 3. Run Spark Batch Transformation Job
    # This task executes the `batch_transformations.py` script.
    # It reads from the raw Delta Lake, transforms/enriches, and writes to a curated Delta Lake.
    # IMPORTANT NOTE: The `docker exec spark` command refers to the `spark-master` service
    # in your `docker-compose.yml`. Ensure the `pyspark_jobs` volume is mounted
    # in the `spark-master` container and Spline JARs are available.
    run_spark_transformation = BashOperator(
        task_id='run_spark_financial_transformation',
        bash_command="""
        docker exec spark-master spark-submit \\
            --packages io.delta:delta-core_2.12:2.4.0,org.postgresql:postgresql:42.6.0 \\
            --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension \\
            --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog \\
            --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \\
            --conf spark.hadoop.fs.s3a.access.key=minioadmin \\
            --conf spark.hadoop.fs.s3a.secret.key=minioadmin \\
            --conf spark.hadoop.fs.s3a.path.style.access=true \\
            --conf spark.spline.producer.url=http://spline-rest:8080/producer \\
            --conf spark.spline.mode=ENABLED \\
            --driver-java-options "-javaagent:/opt/bitnami/spark/jars/spline-agent-bundle-0.7.1.jar" \\
            /opt/bitnami/spark/jobs/batch_transformations.py \\
            s3a://raw-data-bucket/financial_data_delta \\
            s3a://curated-data-bucket/financial_data_curated_full_pipeline
        """,
        doc_md="""
        ### Run Spark Financial Transformation
        Executes a Spark batch job to transform and curate raw financial data.
        This job reads from `raw_financial_transactions_delta`, applies business logic,
        and writes to `financial_data_curated_full_pipeline`.
        Spline is configured to capture lineage automatically.
        """,
    )

    # 4. Validate Data in PostgreSQL (Conceptual Check)
    # IMPORTANT NOTE: This task is a conceptual placeholder for data quality validation.
    # In a real scenario, you would execute actual validation queries against the
    # `financial_data_curated_full_pipeline` table in MinIO using Spark SQL,
    # or integrate with a data quality framework like Great Expectations.
    validate_postgres_data = BashOperator(
        task_id='validate_financial_data_in_postgres',
        bash_command="""
        echo "Simulating data validation check..."
        # Example: A conceptual check to see if the table exists or has records.
        # In a real scenario, you'd execute actual validation queries.
        # Example using Spark SQL directly (assuming Spark container access):
        # docker exec advanced-spark-master spark-sql \\
        #   --packages io.delta:delta-core_2.12:2.4.0 \\
        #   --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension \\
        #   --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog \\
        #   --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \\
        #   --conf spark.hadoop.fs.s3a.access.key=minioadmin \\
        #   --conf spark.hadoop.fs.s3a.secret.key=minioadmin \\
        #   --conf spark.hadoop.fs.s3a.path.style.access=true \\
        #   -e "SELECT COUNT(*) FROM delta.\`s3a://curated-data-bucket/financial_data_curated_full_pipeline\` WHERE is_amount_valid = false;"
        # exit 0 # Ensure the task succeeds for demo purposes
        """,
        doc_md="""
        ### Validate Financial Data
        This is a conceptual task to represent data quality validation.
        In a full implementation, this would involve detailed checks on the
        curated data for completeness, accuracy, and consistency using Spark SQL
        or a dedicated data quality framework.
        """,
    )

    # 5. Ingest OpenMetadata (Post-transformation Metadata Sync)
    # This task triggers the OpenMetadata ingestion connector specifically for the
    # Spark lineage and the new Delta Lake table created by the Spark job.
    # IMPORTANT NOTE: This command runs from within the `openmetadata-ingestion` container.
    # Ensure this container has access to the OpenMetadata server and the necessary
    # connector configurations are mounted/available.
    ingest_openmetadata = BashOperator(
        task_id='ingest_openmetadata_for_financial_data',
        bash_command='docker exec openmetadata-ingestion python '
                     '/opt/openmetadata/examples/workflows/run_metadata_workflow.py '
                     '--config /opt/openmetadata/examples/workflows/spark_lineage_and_s3_delta_connector_config.yaml',
        doc_md="""
        ### Ingest OpenMetadata for Financial Data
        Triggers the OpenMetadata ingestion framework to scan for new metadata
        and lineage related to the transformed financial data, pulling information
        from Spline (for Spark lineage) and MinIO (for Delta Lake table schema).
        """,
    )

    end_pipeline = EmptyOperator(
        task_id='end_full_pipeline',
        doc_md="""
        ### End Full Pipeline
        The end of the data pipeline.
        """,
    )

    # Define task dependencies
    start_ingestion >> prepare_raw_data_delta >> run_spark_transformation
    run_spark_transformation >> validate_postgres_data >> ingest_openmetadata >> end_pipeline

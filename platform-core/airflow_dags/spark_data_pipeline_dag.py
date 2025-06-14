# Description: DAG to orchestrate Spark jobs for a financial data lake pipeline.
# Source: Highlighting Apache Airflow, Advanced Use Case 1 (Orchestrating Spark Jobs).
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

# Define common Spark submit arguments to connect to MinIO and Delta Lake
SPARK_COMMON_CONF = (
    "--packages io.delta:delta-core_2.12:2.4.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 "
    "--conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension "
    "--conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog "
    "--conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 "
    "--conf spark.hadoop.fs.s3a.access.key=minioadmin "
    "--conf spark.hadoop.fs.s3a.secret.key=minioadmin "
    "--conf spark.hadoop.fs.s3a.path.style.access=true "
)

with DAG(
    dag_id='financial_data_lake_pipeline',
    start_date=days_ago(1),
    schedule_interval=timedelta(minutes=5), # Run every 5 minutes for continuous demo
    catchup=False,
    tags=['data_lake', 'spark', 'etl'],
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
    },
    doc_md="""
    ### Financial Data Lake Pipeline
    This DAG orchestrates a full financial data pipeline:
    1.  `ingest_raw_financial_data`: Continuously ingests financial transactions from Kafka to a raw Delta Lake table.
    2.  `transform_curate_financial_data`: Transforms raw financial data from Delta Lake to a curated Delta Lake table.
        This task depends on `ingest_raw_financial_data` to ensure raw data is available.
    """
) as dag:
    # Task 1: Ingest Raw Financial Data from Kafka to Delta Lake
    # This simulates the streaming job, which Airflow would typically ensure is running
    # or trigger for a fixed window. For simplicity here, we trigger a job
    # that runs for a short period to process recent data.
    ingest_raw_financial_data = BashOperator(
        task_id='ingest_raw_financial_data',
        bash_command=f"docker exec -it spark spark-submit {SPARK_COMMON_CONF} "
                     f"/opt/bitnami/spark/jobs/streaming_consumer.py "
                     f"raw_financial_transactions kafka:29092 s3a://raw-data-bucket/financial_data_delta "
                     f"&& sleep 30", # Run for 30s to process a batch and then exit
        doc_md="""
        #### Ingest Raw Financial Data
        This task triggers a Spark Structured Streaming job to ingest financial transaction
        data from Kafka into the raw Delta Lake zone.
        """
    )

    # Task 2: Transform and Curate Financial Data
    # This is a batch job that reads from raw and writes to curated.
    transform_curate_financial_data = BashOperator(
        task_id='transform_curate_financial_data',
        bash_command=f"docker exec -it spark spark-submit {SPARK_COMMON_CONF} "
                     f"/opt/bitnami/spark/jobs/batch_transformations.py "
                     f"s3a://raw-data-bucket/financial_data_delta "
                     f"s3a://curated-data-bucket/financial_data_curated ",
        doc_md="""
        #### Transform and Curate Financial Data
        This task triggers a Spark batch job to read raw financial data from Delta Lake,
        apply transformations, and write it to the curated Delta Lake zone.
        """
    )

    # Define task dependencies
    ingest_raw_financial_data >> transform_curate_financial_data
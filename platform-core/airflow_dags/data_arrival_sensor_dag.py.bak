# Description: DAG using S3KeySensor to trigger on data arrival with SLA.
# Source: Highlighting Apache Airflow, Advanced Use Case 1 (Data-Driven Dependencies & SLA Management).
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor # Requires apache-airflow-providers-amazon
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta

with DAG(
    dag_id='data_arrival_sensor_with_sla',
    start_date=days_ago(1),
    schedule_interval=None, # Triggered manually or by external system
    catchup=False,
    tags=['s3', 'sensor', 'sla'],
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 0,
        'retry_delay': timedelta(minutes=1),
        'sla': timedelta(minutes=10) # SLA: Task must complete within 10 minutes of start
    }
) as dag:
    # Sensor to wait for a specific file pattern in MinIO
    # Note: S3KeySensor by default uses boto3, ensure minio is configured as S3 endpoint
    # For a simpler local test with MinIO, you might need to configure AWS connection
    # in Airflow UI or use a custom sensor. This example assumes basic S3KeySensor can reach MinIO.
    wait_for_financial_data = S3KeySensor(
        task_id='wait_for_new_financial_data_file',
        bucket_name='raw-data-bucket',
        # Key should be a pattern that indicates a new partition/file is ready
        # e.g., for daily partitions: 'financial_data_delta/daily_load_{{ ds }}/_SUCCESS'
        # For streaming, you might look for a new parquet file in the latest micro-batch directory
        # For a simpler test, just look for any new parquet file in the path
        prefix='financial_data_delta/', # Just checks if files exist under this prefix
        wildcard_match=True, # Allows prefix/wildcard matching
        poke_interval=5, # Check every 5 seconds
        timeout=60 * 60, # Timeout after 1 hour if file not found
        # In a real environment, you'd specify aws_conn_id, e.g., aws_conn_id='aws_default_minio'
    )
    # Once data arrives, trigger the transformation
    # This BashOperator calls a Spark job.
    SPARK_COMMON_CONF = (
        "--packages io.delta:delta-core_2.12:2.4.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 "
        "--conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension "
        "--conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog "
        "--conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 "
        "--conf spark.hadoop.fs.s3a.access.key=minioadmin "
        "--conf spark.hadoop.fs.s3a.secret.key=minioadmin "
        "--conf spark.hadoop.fs.s3a.path.style.access=true "
    )
    run_transformation = BashOperator(
        task_id='transform_financial_data_after_arrival',
        bash_command=f"""
            echo "New financial data detected! Starting transformation..."
            docker exec spark spark-submit \\
                {SPARK_COMMON_CONF} \\
                /opt/bitnami/spark/jobs/batch_transformations.py \\
                s3a://raw-data-bucket/financial_data_delta \\
                s3a://curated-data-bucket/financial_data_curated_sensor_triggered
        """,
        sla=timedelta(minutes=5) # This task must complete within 5 minutes of starting
    )
    wait_for_financial_data >> run_transformation
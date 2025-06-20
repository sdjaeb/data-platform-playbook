from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

with DAG(
    dag_id='data_arrival_sensor_dag',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['example', 's3', 'sensor'],
) as dag:
    # Sensor to wait for a specific file pattern in MinIO
    # Note: S3KeySensor by default uses boto3, ensure minio is configured as S3 endpoint
    # For a simpler local test with MinIO, you might need to configure AWS connection
    # in Airflow UI or use a custom sensor. This example assumes basic S3KeySensor can reach MinIO.
    wait_for_financial_data = S3KeySensor(
        task_id='wait_for_new_financial_data_file',
        bucket_name='raw-data-bucket', # Assuming this bucket is created by bootstrap.sh
        bucket_key='financial_data_delta/placeholder_file_success.txt', # Added a placeholder bucket_key
        prefix='financial_data_delta/', # Just checks if files exist under this prefix
        wildcard_match=True, # Allows prefix/wildcard matching
        aws_conn_id='aws_default', # This connection needs to be configured in Airflow
        poke_interval=5, # Check every 5 seconds
        timeout=60 * 5, # Timeout after 5 minutes
        mode='poke',
    )

    data_arrived_task = BashOperator(
        task_id='data_arrived_notification',
        bash_command='echo "Financial data file arrived! Proceeding with processing (conceptual)."',
    )

    wait_for_financial_data >> data_arrived_task

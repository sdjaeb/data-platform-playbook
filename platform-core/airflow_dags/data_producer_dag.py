# Description: DAG to simulate data production and push XComs.
# Source: Highlighting Apache Airflow, Advanced Use Case 3 (Cross-DAG Dependencies and Data Sharing).
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta # Import datetime for start_date
import json # Not strictly used in this mock but useful for real data

def push_xcom_data(**kwargs):
    """Pushes a mock file path or transaction ID as an XCom."""
    # kwargs['ds_nodash'] provides the execution date in YYYYMMDD format
    file_path = f"/tmp/processed_file_{kwargs['ds_nodash']}.parquet"
    print(f"Simulating processing and pushing file path: {file_path}")
    # The 'ti' (task instance) object is provided by provide_context=True
    kwargs['ti'].xcom_push(key='processed_file_path', value=file_path)

with DAG(
    dag_id='data_producer_dag', # Keep dag_id
    start_date=datetime(2023, 1, 1), # Use fixed datetime for start_date
    schedule_interval=timedelta(hours=1), # Run hourly
    catchup=False,
    tags=['xcom_demo', 'producer'],
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
    },
    doc_md="""
    ### Data Producer DAG
    This DAG simulates a data ingestion process and pushes a 'processed_file_path'
    to XCom for consumption by another DAG.
    """
) as producer_dag:
    start_task = BashOperator(
        task_id='start_producer',
        bash_command='echo "Producer DAG started."',
    )

    process_and_push = PythonOperator(
        task_id='process_and_push_data',
        python_callable=push_xcom_data,
        provide_context=True, # Allows access to task instance (ti)
    )

    end_task = BashOperator(
        task_id='end_producer',
        bash_command='echo "Producer DAG finished."',
    )

    start_task >> process_and_push >> end_task
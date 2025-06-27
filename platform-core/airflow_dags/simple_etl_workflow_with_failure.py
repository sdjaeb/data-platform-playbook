# Description: DAG demonstrating failure handling and retries.
# Source: Highlighting Apache Airflow, Advanced Use Case 2 (Handling Failures and Retries).
from airflow import DAG
from airflow.operators.bash import BashOperator # Keep BashOperator
from datetime import datetime, timedelta # Use datetime for start_date
import os

with DAG(
    dag_id='simple_etl_workflow_with_failure', # Changed DAG ID from original simple_etl_workflow
    start_date=datetime(2023, 1, 1), # Use fixed datetime for start_date
    schedule_interval=None,
    catchup=False,
    tags=['example', 'failure_demo'],
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 2, # Increase retries to 2 for this demo (total 3 attempts: initial + 2 retries)
        'retry_delay': timedelta(seconds=10), # Retry after 10 seconds
    },
    doc_md="""
    ### Simple ETL Workflow with Failure Demo
    This DAG demonstrates retry mechanisms. The `fail_once_then_succeed` task
    is designed to fail on its first attempt and succeed on retry.
    """
) as dag:
    # Task that will fail once then succeed
    # Uses a temporary file to simulate transient failure.
    # On first run, marker is not found, creates it, and exits with error (1).
    # On retry, marker is found, deletes it, and exits successfully (0).
    fail_once_then_succeed = BashOperator(
        task_id='fail_once_then_succeed',
        bash_command="""
        if [ ! -f /tmp/airflow_failure_marker.txt ]; then
            echo "Creating failure marker and failing for the first time..."
            touch /tmp/airflow_failure_marker.txt
            exit 1
        else
            echo "Marker found, succeeding now!"
            rm /tmp/airflow_failure_marker.txt
        fi
        """,
        retries=1, # This task specifically retries once (total 2 attempts including initial)
        retry_delay=timedelta(seconds=5), # Wait 5 seconds before retrying
        doc_md="""
        #### Fail Once Then Succeed
        This task is designed to fail on its first run and succeed on a retry.
        """
    )

    # A dependent task that will only run after the first succeeds
    downstream_success = BashOperator(
        task_id='downstream_success',
        bash_command='echo "Downstream task succeeded after retry!"',
        doc_md="""
        #### Downstream Success
        This task only runs if the upstream task succeeds (possibly after a retry).
        """
    )

    fail_once_then_succeed >> downstream_success
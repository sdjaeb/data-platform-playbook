# Description: Basic ETL workflow DAG.
# Source: Highlighting Apache Airflow, Basic Use Case.
from airflow import DAG
from airflow.operators.bash import BashOperator # Keep BashOperator
from datetime import datetime, timedelta # Use datetime for start_date

with DAG(
    dag_id='simple_etl_workflow',
    start_date=datetime(2023, 1, 1), # Use fixed datetime for start_date
    schedule_interval=None, # Set to None for manual trigger, or use a cron expression '0 0 * * *' for daily
    catchup=False, # Do not backfill past runs
    tags=['example', 'basic_etl'],
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    },
    doc_md="""
    ### Simple ETL Workflow
    This DAG demonstrates a very basic ETL process with two tasks:
    1. `extract_data`: Simulates data extraction by printing a message.
    2. `transform_and_load`: Simulates data transformation and loading by printing another message.
    """
) as dag:
    # Task 1: Simulate Data Extraction
    extract_data = BashOperator(
        task_id='extract_data',
        bash_command='echo "Extracting data from source..." && sleep 5',
        doc_md="""
        #### Extract Data
        This task simulates extracting data from a source system.
        It simply prints a message and sleeps for 5 seconds.
        """
    )

    # Task 2: Simulate Data Transformation and Loading
    transform_and_load = BashOperator(
        task_id='transform_and_load',
        bash_command='echo "Transforming and loading data into destination..." && sleep 7',
        doc_md="""
        #### Transform and Load
        This task simulates transforming the extracted data and loading it into a target.
        It prints a message and sleeps for 7 seconds.
        """
    )

    # Define the task dependencies
    extract_data >> transform_and_load
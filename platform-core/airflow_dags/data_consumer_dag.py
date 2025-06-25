# Description: DAG consuming data from another DAG using XComs and ExternalTaskSensor.
# Source: Highlighting Apache Airflow, Advanced Use Case 3 (Cross-DAG Dependencies and Data Sharing).
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.sensors.external_task import ExternalTaskSensor # Keep ExternalTaskSensor
from datetime import timedelta

def pull_xcom_data(**kwargs):
    """Pulls the XCom data from the producer DAG."""
    ti = kwargs['ti']
    # Pull from data_producer_dag's 'process_and_push_data' task
    # on the same logical date (execution_date)
    processed_file_path = ti.xcom_pull(
        dag_id='data_producer_dag',
        task_ids='process_and_push_data',
        key='processed_file_path',
        include_prior_dates=False # Only look for XComs from the current execution date
    )
    if processed_file_path:
        print(f"Consumer DAG received processed file path from producer: {processed_file_path}")
        # You would use this path to further process data, e.g., in a Spark job
    else:
        print("No processed file path received from producer DAG.")
        raise ValueError("Failed to retrieve XCom from producer DAG.") # Fail if not found

with DAG(
    dag_id='data_consumer_dag', # Keep dag_id
    start_date=datetime(2023, 1, 1), # Use fixed datetime for start_date
    schedule_interval=timedelta(hours=1), # Also run hourly, aligned with producer
    catchup=False,
    tags=['xcom_demo', 'consumer'],
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
    },
    doc_md="""
    ### Data Consumer DAG
    This DAG demonstrates consuming data (a file path) from another DAG (data_producer_dag)
    using ExternalTaskSensor and XComs.
    """
) as consumer_dag:
    # Sensor to wait for the producer DAG to complete its specific task
    wait_for_producer_data = ExternalTaskSensor(
        task_id='wait_for_producer_data',
        external_dag_id='data_producer_dag',
        external_task_id='process_and_push_data', # Wait for this specific task
        mode='poke', # Continuously check until condition met
        poke_interval=5, # Check every 5 seconds
        timeout=600, # Timeout after 10 minutes
        allowed_states=['success'],
        failed_states=['failed', 'skipped'],
        # The execution_delta ensures that the sensor waits for the *same* logical execution date
        # If producer and consumer have same schedule_interval, this is usually timedelta(0)
        execution_delta=None # For same schedule interval, look at same execution_date
    )

    consume_xcom_data = PythonOperator(
        task_id='consume_xcom_data',
        python_callable=pull_xcom_data,
        provide_context=True,
    )

    finish_consumer = BashOperator(
        task_id='finish_consumer',
        bash_command='echo "Consumer DAG finished processing data."',
    )

    wait_for_producer_data >> consume_xcom_data >> finish_consumer
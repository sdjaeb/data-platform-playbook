from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from datetime import datetime

with DAG(
    dag_id='trigger_generators',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['generators', 'api'],
    doc_md="""
    ### Trigger Data Generators DAG
    This DAG provides tasks to start, stop, and send malformed data for each data generator service.
    It uses Airflow HTTP connections defined in the environment:
    - `financial_generator_api`
    - `insurance_generator_api`
    - `sports_generator_api`
    """
) as dag:
    # --- Financial Data Generator Tasks ---
    start_financial = SimpleHttpOperator(
        task_id='start_financial',
        http_conn_id='financial_generator_api',
        endpoint='start',
        method='GET'
    )

    stop_financial = SimpleHttpOperator(
        task_id='stop_financial',
        http_conn_id='financial_generator_api',
        endpoint='stop',
        method='GET'
    )

    send_malformed_financial = SimpleHttpOperator(
        task_id='send_malformed_financial',
        http_conn_id='financial_generator_api',
        endpoint='malformed',
        method='GET'
    )

    # --- Insurance Data Generator Tasks ---
    start_insurance = SimpleHttpOperator(
        task_id='start_insurance',
        http_conn_id='insurance_generator_api',
        endpoint='start',
        method='GET'
    )

    stop_insurance = SimpleHttpOperator(
        task_id='stop_insurance',
        http_conn_id='insurance_generator_api',
        endpoint='stop',
        method='GET'
    )

    send_malformed_insurance = SimpleHttpOperator(
        task_id='send_malformed_insurance',
        http_conn_id='insurance_generator_api',
        endpoint='malformed',
        method='GET'
    )

    # --- Sports Data Generator Tasks ---
    start_sports = SimpleHttpOperator(
        task_id='start_sports',
        http_conn_id='sports_generator_api',
        endpoint='start',
        method='GET'
    )

    stop_sports = SimpleHttpOperator(
        task_id='stop_sports',
        http_conn_id='sports_generator_api',
        endpoint='stop',
        method='GET'
    )

    send_malformed_sports = SimpleHttpOperator(
        task_id='send_malformed_sports',
        http_conn_id='sports_generator_api',
        endpoint='malformed',
        method='GET'
    )
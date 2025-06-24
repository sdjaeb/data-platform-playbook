from airflow import DAG
from airflow.operators.http_operator import SimpleHttpOperator
from datetime import datetime

with DAG('trigger_generators', start_date=datetime(2024, 1, 1), schedule_interval=None, catchup=False) as dag:
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
        task_id='malformed_financial',
        http_conn_id='financial_generator_api',
        endpoint='malformed',
        method='GET'
    )
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
    send_insurance_malformed = SimpleHttpOperator(
        task_id='malformed_insurance',
        http_conn_id='insurance_generator_api',
        endpoint='malformed',
        method='GET'
    )
    start_sports = SimpleHttpOperator(
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
    send_sports_malformed = SimpleHttpOperator(
        task_id='malformed_financial',
        http_conn_id='financial_generator_api',
        endpoint='malformed',
        method='GET'
    )
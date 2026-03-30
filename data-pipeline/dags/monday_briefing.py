"""
DAG: monday_briefing
Coleta dados de mercado e macro toda segunda-feira, carrega no PostgreSQL e
dispara as transformações dbt (staging views + gold tables).

Fluxo:
  [extract_bcb, extract_yfinance, extract_cvm] → load_to_postgres → dbt_run
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="monday_briefing",
    description="Coleta BCB + yFinance + CVM, carrega no PostgreSQL e roda dbt",
    schedule_interval="0 8 * * 1",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["ingestão", "dbt"],
) as dag:

    def _extract_bcb():
        from extractors.macro_bcb import extract_bcb
        extract_bcb()

    def _extract_yfinance():
        from extractors.market_yfinance import extract_yfinance
        from utils.company_config import COMPANIES
        extract_yfinance(tickers=list(COMPANIES.keys()))

    def _extract_cvm():
        from extractors.fundamentals_cvm import extract_cvm
        from utils.company_config import COMPANIES
        extract_cvm(tickers=list(COMPANIES.keys()))

    def _load_to_postgres():
        from loaders.postgres_loader import load_all_parquets
        load_all_parquets()

    def _dbt_run():
        from loaders.postgres_loader import run_dbt
        run_dbt()

    extract_bcb = PythonOperator(
        task_id="extract_bcb",
        python_callable=_extract_bcb,
    )

    extract_yfinance = PythonOperator(
        task_id="extract_yfinance",
        python_callable=_extract_yfinance,
    )

    extract_cvm = PythonOperator(
        task_id="extract_cvm",
        python_callable=_extract_cvm,
    )

    load_to_postgres = PythonOperator(
        task_id="load_to_postgres",
        python_callable=_load_to_postgres,
    )

    dbt_run = PythonOperator(
        task_id="dbt_run",
        python_callable=_dbt_run,
    )

    [extract_bcb, extract_yfinance, extract_cvm] >> load_to_postgres >> dbt_run

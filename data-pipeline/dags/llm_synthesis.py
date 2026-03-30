"""
DAG: llm_synthesis
Gera o relatório semanal de síntese usando LLM (Anthropic/OpenAI).
Roda toda segunda-feira às 09h, após o monday_briefing ter carregado os dados.

Fluxo:
  fetch_context (RAG das tabelas gold) → generate_report (LLM)
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
    dag_id="llm_synthesis",
    description="Gera relatório de síntese semanal via LLM com contexto das tabelas gold",
    schedule_interval="0 9 * * 1",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["llm", "síntese"],
) as dag:

    def _fetch_context():
        from synthesis.rag import fetch_context
        return fetch_context()

    def _generate_report(**context):
        ctx = context["ti"].xcom_pull(task_ids="fetch_context")
        from synthesis.llm_report import generate_report
        generate_report(ctx)

    fetch_context = PythonOperator(
        task_id="fetch_context",
        python_callable=_fetch_context,
    )

    generate_report = PythonOperator(
        task_id="generate_report",
        python_callable=_generate_report,
        provide_context=True,
    )

    fetch_context >> generate_report

"""
DAG: site_ingestion
Monitora a pasta uploads/ e processa arquivos novos automaticamente.

Fluxo:
  1. FileSensor detecta novo arquivo em uploads/
  2. parse_and_load: valida nome, extrai conteúdo, salva bronze + silver
  3. Arquivo movido para uploads/processed/ após sucesso

Adicionar nova empresa: apenas atualizar COMPANIES em company_config.py
"""

import os
import shutil
from pathlib import Path
from datetime import timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.dates import days_ago

UPLOADS_DIR   = Path("/opt/airflow/uploads")
PROCESSED_DIR = UPLOADS_DIR / "processed"

DEFAULT_ARGS = {
    "owner":            "airflow",
    "depends_on_past":  False,
    "email_on_failure": False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=2),
}


def _find_new_file() -> str:
    """Retorna o path do primeiro arquivo novo em uploads/."""
    for f in sorted(UPLOADS_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() in (".pdf", ".xlsx", ".mp3", ".mp4", ".wav"):
            return str(f)
    raise FileNotFoundError(f"Nenhum arquivo novo encontrado em {UPLOADS_DIR}")


def parse_and_load_task(**context):
    from utils.file_parser import get_parser
    from utils.site_writer import write_all

    filepath = Path(_find_new_file())
    print(f"[INGEST] Processando: {filepath.name}")

    parser = get_parser(filepath)

    # parse() ou transcribe() dependendo do tipo
    if hasattr(parser, "parse"):
        tables = parser.parse()
    else:
        tables = parser.transcribe()

    write_all(tables)

    # Move para processed/
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dest = PROCESSED_DIR / filepath.name
    shutil.move(str(filepath), str(dest))
    print(f"[INGEST] Arquivo movido para {dest}")


with DAG(
    dag_id="site_ingestion",
    description="Monitora uploads/ e processa PDFs/Excels do site de RI",
    schedule_interval=None,      # triggered pelo sensor ou manualmente
    start_date=days_ago(1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["ingestion", "site", "pdf"],
) as dag:

    t_sensor = FileSensor(
        task_id="wait_for_file",
        filepath=str(UPLOADS_DIR / "*"),
        fs_conn_id="fs_default",
        poke_interval=30,        # verifica a cada 30 segundos
        timeout=60 * 60 * 4,    # espera até 4 horas
        mode="poke",
        doc_md="Aguarda novo arquivo em uploads/.",
    )

    t_process = PythonOperator(
        task_id="parse_and_load",
        python_callable=parse_and_load_task,
        doc_md="Extrai conteúdo do arquivo, salva bronze e silver.",
    )

    t_sensor >> t_process

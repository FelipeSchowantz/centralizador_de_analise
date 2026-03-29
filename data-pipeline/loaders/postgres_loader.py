"""
Loader — PostgreSQL
Lê os Parquets da camada bronze e carrega nas tabelas de staging do PostgreSQL.
As transformações finais são feitas pelo dbt.
"""

import os
import psycopg2
import pandas as pd
from pathlib import Path
from psycopg2.extras import execute_values

# Parâmetros de conexão
PG_HOST     = os.getenv("PG_HOST",     "localhost")
PG_PORT     = os.getenv("PG_PORT",     "5432")
PG_DB       = os.getenv("PG_DB",       "airflow")
PG_USER     = os.getenv("PG_USER",     "airflow")
PG_PASSWORD = os.getenv("PG_PASSWORD", "airflow")

BRONZE_PATH = Path(__file__).resolve().parents[2] / "data-lakehouse" / "bronze"

TABLE_MAP = {
    "bcb":      "staging.raw_bcb",
    "yfinance": "staging.raw_yfinance",
    "cvm":      "staging.raw_cvm",
}


def get_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def load_source(source: str) -> None:
    """Carrega o Parquet mais recente de uma fonte no PostgreSQL via psycopg2."""
    source_path = BRONZE_PATH / source
    parquets = sorted(source_path.glob("*.parquet"))
    if not parquets:
        print(f"[PG] Nenhum Parquet encontrado para {source}")
        return

    latest = parquets[-1]
    df = pd.read_parquet(latest)

    # Converte timestamps para string para evitar problemas de tipo
    for col in df.select_dtypes(include=["datetimetz", "datetime64[ns, UTC]"]).columns:
        df[col] = df[col].astype(str)

    table = TABLE_MAP[source]
    columns = list(df.columns)
    values  = [tuple(row) for row in df.itertuples(index=False, name=None)]

    col_str = ", ".join(f'"{c}"' for c in columns)
    sql = f'INSERT INTO {table} ({col_str}) VALUES %s'

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            execute_values(cur, sql, values)
        conn.commit()
        print(f"[PG] {len(df)} linhas carregadas em {table} a partir de {latest.name}")
    except Exception as e:
        conn.rollback()
        print(f"[PG] Erro ao carregar {source}: {e}")
        raise
    finally:
        conn.close()


def load_all_parquets() -> None:
    """Carrega todas as fontes no PostgreSQL."""
    for source in TABLE_MAP:
        load_source(source)


if __name__ == "__main__":
    load_all_parquets()

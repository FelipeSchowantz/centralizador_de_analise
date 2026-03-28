"""
Loader — PostgreSQL
Lê os Parquets da camada raw e carrega nas tabelas de staging do PostgreSQL.
As transformações finais são feitas pelo dbt.
"""

import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

PG_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql://airflow:airflow@localhost:5432/charles_river"
)

BRONZE_PATH = Path(__file__).resolve().parents[2] / "data-lakehouse" / "bronze"

TABLE_MAP = {
    "bcb":      "staging.raw_bcb",
    "yfinance": "staging.raw_yfinance",
    "cvm":      "staging.raw_cvm",
}


def load_source(source: str) -> None:
    """Carrega o Parquet mais recente de uma fonte no PostgreSQL."""
    source_path = BRONZE_PATH / source
    parquets = sorted(source_path.glob("*.parquet"))
    if not parquets:
        print(f"[PG] Nenhum Parquet encontrado para {source}")
        return

    latest = parquets[-1]
    df = pd.read_parquet(latest)
    engine = create_engine(PG_URL)

    table = TABLE_MAP[source]
    schema, tbl = table.split(".")
    df.to_sql(tbl, engine, schema=schema, if_exists="append", index=False)
    print(f"[PG] {len(df)} linhas carregadas em {table} a partir de {latest.name}")


def load_all_parquets() -> None:
    """Carrega todas as fontes no PostgreSQL."""
    for source in TABLE_MAP:
        load_source(source)


if __name__ == "__main__":
    load_all_parquets()

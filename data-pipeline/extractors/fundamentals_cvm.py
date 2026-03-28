"""
Extrator — CVM (Comissão de Valores Mobiliários)
Fonte: dados.cvm.gov.br (pública, sem autenticação)
Coleta: linhas de DRE via ITR/DFP
Saída:
  - __main__ (teste): CSV bruto em testes/cvm/ + Parquet filtrado em testes/cvm/
  - Airflow:          Parquet filtrado em data-lakehouse/bronze/cvm/
"""

import requests
import pandas as pd
import zipfile
import io
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRONZE_PATH = ROOT / "data-lakehouse" / "bronze" / "cvm"
TEST_PATH   = ROOT / "testes" / "cvm"

# CNPJs das empresas (necessário para filtrar nos arquivos da CVM)
EMPRESA_CNPJ = {
    "ASAI3": "06.057.223/0001-71",  # Assaí Atacadista
    "PRIO3": "10.629.105/0001-68",  # PetroRio
    "RENT3": "16.670.085/0001-55",  # Localiza
}

# Linhas de DRE de interesse (conta contábil padrão CVM)
CONTAS_DRE = [
    "3.01",   # Receita Líquida
    "3.05",   # EBIT
    "3.11",   # Lucro Líquido
    "3.07",   # Depreciação e Amortização (quando disponível)
]

CVM_ITR_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"


def _download_itr(ano: int) -> pd.DataFrame:
    """Baixa o ZIP da CVM e extrai o CSV de DRE consolidado."""
    filename = f"itr_cia_aberta_{ano}.zip"
    url = CVM_ITR_URL + filename
    print(f"[CVM] Baixando {url}")
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        csv_name = [n for n in z.namelist() if "DRE_con" in n][0]
        print(f"[CVM] Extraindo {csv_name}")
        with z.open(csv_name) as f:
            df = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str)
    return df


def _filter(df_raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Filtra pelas empresas e contas contábeis de interesse."""
    cnpjs = [EMPRESA_CNPJ[t] for t in tickers if t in EMPRESA_CNPJ]
    cnpjs_clean = [c.replace(".", "").replace("/", "").replace("-", "") for c in cnpjs]

    df_raw["CNPJ_CIA"] = df_raw["CNPJ_CIA"].str.replace(r"\D", "", regex=True)

    df = df_raw[
        df_raw["CNPJ_CIA"].isin(cnpjs_clean) &
        df_raw["CD_CONTA"].isin(CONTAS_DRE)
    ].copy()

    df["_extracted_at"] = pd.Timestamp.utcnow()
    return df


def extract_cvm(tickers: list[str], out_path: Path = BRONZE_PATH) -> None:
    """
    Coleta DRE da CVM, filtra empresas e salva Parquet.
    Usado pelo Airflow.
    """
    ano_atual = date.today().year

    try:
        df_raw = _download_itr(ano=ano_atual)
    except Exception as e:
        print(f"[CVM] Tentando ano anterior: {e}")
        df_raw = _download_itr(ano=ano_atual - 1)

    df_filtered = _filter(df_raw, tickers)

    out_path.mkdir(parents=True, exist_ok=True)
    parquet_file = out_path / f"cvm_{date.today().isoformat()}.parquet"
    df_filtered.to_parquet(parquet_file, index=False)
    print(f"[CVM] {len(df_filtered)} linhas salvas em {parquet_file}")


if __name__ == "__main__":
    ano_atual = date.today().year

    try:
        df_raw = _download_itr(ano=ano_atual)
    except Exception as e:
        print(f"[CVM] Tentando ano anterior: {e}")
        df_raw = _download_itr(ano=ano_atual - 1)

    TEST_PATH.mkdir(parents=True, exist_ok=True)
    csv_file = TEST_PATH / f"cvm_raw_{date.today().isoformat()}.csv"
    df_raw.to_csv(csv_file, index=False)
    print(f"[CVM] CSV bruto salvo em {csv_file}")

"""
Extrator — CVM (Comissão de Valores Mobiliários)
Fonte: dados.cvm.gov.br (pública, sem autenticação)
Coleta: linhas de DRE via ITR/DFP
Saída: Parquet em data-lakehouse/raw/cvm/
"""

import requests
import pandas as pd
import zipfile
import io
from datetime import date
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[2] / "data-lakehouse" / "raw" / "cvm"

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


def _download_itr(ano: int, trimestre: int) -> pd.DataFrame:
    """Baixa e descomprime o arquivo de DRE do trimestre da CVM."""
    filename = f"itr_cia_aberta_DRE_con_{ano}.zip"
    url = CVM_ITR_URL + filename
    print(f"[CVM] Baixando {url}")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        csv_name = [n for n in z.namelist() if "DRE_con" in n][0]
        with z.open(csv_name) as f:
            df = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str)
    return df


def extract_cvm(tickers: list[str]) -> None:
    """
    Coleta linhas selecionadas da DRE para cada empresa e salva em Parquet.
    Usa o ITR (trimestral) do ano corrente.
    """
    ano_atual = date.today().year
    cnpjs = [EMPRESA_CNPJ[t] for t in tickers if t in EMPRESA_CNPJ]

    try:
        df_raw = _download_itr(ano=ano_atual, trimestre=None)
    except Exception as e:
        print(f"[CVM] Tentando ano anterior: {e}")
        df_raw = _download_itr(ano=ano_atual - 1, trimestre=None)

    # Normaliza CNPJ para comparação
    df_raw["CNPJ_CIA"] = df_raw["CNPJ_CIA"].str.replace(r"\D", "", regex=True)
    cnpjs_clean = [c.replace(".", "").replace("/", "").replace("-", "") for c in cnpjs]

    df_filtered = df_raw[
        df_raw["CNPJ_CIA"].isin(cnpjs_clean) &
        df_raw["CD_CONTA"].isin(CONTAS_DRE)
    ].copy()

    df_filtered["_extracted_at"] = pd.Timestamp.utcnow()

    out_path = RAW_PATH / f"cvm_{date.today().isoformat()}.parquet"
    RAW_PATH.mkdir(parents=True, exist_ok=True)
    df_filtered.to_parquet(out_path, index=False)
    print(f"[CVM] {len(df_filtered)} linhas salvas em {out_path}")


if __name__ == "__main__":
    extract_cvm(tickers=["ASAI3", "PRIO3", "RENT3"])

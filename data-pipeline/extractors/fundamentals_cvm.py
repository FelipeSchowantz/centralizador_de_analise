"""
Extrator — CVM (Comissão de Valores Mobiliários)
Fonte: dados.cvm.gov.br (pública, sem autenticação)
Coleta: DRE, Balanço Patrimonial (Ativo+Passivo) e Fluxo de Caixa via ITR consolidado
Saída:
  - __main__ (teste): CSV bruto em testes/cvm/
  - Airflow:          Parquet em data-lakehouse/bronze/cvm/
"""

import requests
import pandas as pd
import zipfile
import io
from datetime import date
from pathlib import Path

ROOT        = Path(__file__).resolve().parents[2]
BRONZE_PATH = ROOT / "data-lakehouse" / "bronze" / "cvm"
TEST_PATH   = ROOT / "testes" / "cvm"

# CNPJs sem formatação
EMPRESA_CNPJ = {
    "ASAI3": "06057223000171",
    "PRIO3": "10629105000168",
    "RENT3": "16670085000155",
}

# CSVs dentro do ZIP que nos interessam → prefixo de conta CVM
STATEMENT_MAP = {
    "DRE_con":    "3.",   # Demonstração de Resultado
    "BPA_con":    "1.",   # Balanço Patrimonial — Ativo
    "BPP_con":    "2.",   # Balanço Patrimonial — Passivo e PL
    "DFC_MI_con": "6.",   # Fluxo de Caixa (método indireto)
}

CVM_ITR_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"


def _download_zip(ano: int) -> zipfile.ZipFile:
    """Baixa o ZIP anual da CVM e retorna o objeto ZipFile em memória."""
    url = CVM_ITR_URL + f"itr_cia_aberta_{ano}.zip"
    print(f"[CVM] Baixando {url}")
    resp = requests.get(url, timeout=180)
    resp.raise_for_status()
    return zipfile.ZipFile(io.BytesIO(resp.content))


def _extract_statement(zf: zipfile.ZipFile, key: str) -> pd.DataFrame:
    """Extrai um CSV específico do ZIP pelo prefixo do nome."""
    matches = [n for n in zf.namelist() if key in n]
    if not matches:
        print(f"[CVM] CSV '{key}' não encontrado no ZIP")
        return pd.DataFrame()
    with zf.open(matches[0]) as f:
        df = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str)
    print(f"[CVM] '{matches[0]}' — {len(df)} linhas brutas")
    return df


def _filter(df: pd.DataFrame, tickers: list[str], conta_prefix: str) -> pd.DataFrame:
    """Filtra por empresa e prefixo de conta contábil."""
    cnpjs = [EMPRESA_CNPJ[t] for t in tickers if t in EMPRESA_CNPJ]
    df["CNPJ_CIA"] = df["CNPJ_CIA"].str.replace(r"\D", "", regex=True)
    return df[
        df["CNPJ_CIA"].isin(cnpjs) &
        df["CD_CONTA"].str.startswith(conta_prefix)
    ].copy()


def extract_cvm(tickers: list[str], out_path: Path = BRONZE_PATH) -> None:
    """
    Baixa o ZIP da CVM, extrai DRE + BP + CF, filtra empresas e salva Parquet único.
    """
    ano = date.today().year
    try:
        zf = _download_zip(ano)
    except Exception as e:
        print(f"[CVM] Tentando ano anterior: {e}")
        zf = _download_zip(ano - 1)

    frames = []
    for key, prefix in STATEMENT_MAP.items():
        df_raw  = _extract_statement(zf, key)
        if df_raw.empty:
            continue
        df_filt = _filter(df_raw, tickers, prefix)
        df_filt["_statement"] = key
        frames.append(df_filt)

    if not frames:
        raise RuntimeError("[CVM] Nenhum dado coletado.")

    result = pd.concat(frames, ignore_index=True)
    result["_extracted_at"] = pd.Timestamp.utcnow()

    out_path.mkdir(parents=True, exist_ok=True)
    out_file = out_path / f"cvm_{date.today().isoformat()}.parquet"
    result.to_parquet(out_file, index=False)
    print(f"[CVM] {len(result)} linhas salvas em {out_file}")


if __name__ == "__main__":
    ano = date.today().year
    try:
        zf = _download_zip(ano)
    except Exception as e:
        print(f"[CVM] Tentando ano anterior: {e}")
        zf = _download_zip(ano - 1)

    TEST_PATH.mkdir(parents=True, exist_ok=True)
    for key, _ in STATEMENT_MAP.items():
        df = _extract_statement(zf, key)
        if not df.empty:
            out = TEST_PATH / f"cvm_raw_{key}_{date.today().isoformat()}.csv"
            df.to_csv(out, index=False)
            print(f"[CVM] CSV salvo em {out}")

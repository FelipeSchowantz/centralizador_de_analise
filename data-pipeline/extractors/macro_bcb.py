"""
Extrator — Banco Central do Brasil (BCB)
Fonte: api.bcb.gov.br (pública, sem autenticação)
Saída: Parquet em data-lakehouse/raw/bcb/
"""

import pandas as pd
from python_bcb import sgs
from datetime import date, timedelta
from pathlib import Path

# ── Séries do Banco Central ──────────────────────────────────────────────────
BCB_SERIES = {
    "selic_meta":        432,   # Taxa SELIC (% a.a.)
    "ipca_mensal":       433,   # IPCA variação mensal (%)
    "desemprego":        24369, # Taxa de desemprego PNAD (%)
    "cambio_usd_brl":    1,     # Taxa de câmbio USD/BRL (venda)
    "balanco_comercial": 22707, # Saldo da balança comercial (US$ milhões)
}

RAW_PATH = Path(__file__).resolve().parents[2] / "data-lakehouse" / "raw" / "bcb"


def extract_bcb(lookback_days: int = 365) -> None:
    """
    Coleta as séries macro do BCB dos últimos `lookback_days` dias
    e salva em Parquet particionado por data de execução.
    """
    start = (date.today() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end   = date.today().strftime("%Y-%m-%d")

    frames = []
    for name, codigo in BCB_SERIES.items():
        try:
            df = sgs.get({name: codigo}, start=start, end=end)
            frames.append(df)
            print(f"[BCB] {name} — {len(df)} registros coletados")
        except Exception as e:
            print(f"[BCB] ERRO ao coletar {name} (série {codigo}): {e}")

    if not frames:
        raise RuntimeError("[BCB] Nenhuma série coletada. Verifique a conexão.")

    result = pd.concat(frames, axis=1).reset_index()
    result.rename(columns={"index": "data"}, inplace=True)
    result["_extracted_at"] = pd.Timestamp.utcnow()

    out_path = RAW_PATH / f"bcb_{date.today().isoformat()}.parquet"
    RAW_PATH.mkdir(parents=True, exist_ok=True)
    result.to_parquet(out_path, index=False)
    print(f"[BCB] Salvo em {out_path}")


if __name__ == "__main__":
    extract_bcb()

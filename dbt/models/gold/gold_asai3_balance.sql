-- gold_asai3_balance.sql
-- ASAI3 — Balanço Patrimonial (Ativo 1.xx + Passivo/PL 2.xx)

select
    "DT_REFER"      as data_referencia,
    "DT_FIM_EXERC"  as data_fim_exercicio,
    "CD_CONTA"      as codigo_conta,
    "DS_CONTA"      as descricao_conta,
    "VL_CONTA"      as valor,
    "ESCALA_MOEDA"  as escala,
    _extracted_at
from {{ ref('stg_cvm') }}
where "CNPJ_CIA" = '06057223000171'
  and ("CD_CONTA" like '1.%' or "CD_CONTA" like '2.%')
order by "DT_REFER" desc, "CD_CONTA"

-- gold_prio3_cf.sql
-- PRIO3 — Fluxo de Caixa

select
    "DT_REFER"      as data_referencia,
    "DT_FIM_EXERC"  as data_fim_exercicio,
    "CD_CONTA"      as codigo_conta,
    "DS_CONTA"      as descricao_conta,
    "VL_CONTA"      as valor,
    "ESCALA_MOEDA"  as escala,
    _extracted_at
from {{ ref('stg_cvm') }}
where "CNPJ_CIA" = '10629105000168'
  and "CD_CONTA" like '6.%'
order by "DT_REFER" desc, "CD_CONTA"

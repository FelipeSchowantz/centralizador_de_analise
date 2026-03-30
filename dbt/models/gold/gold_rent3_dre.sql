-- gold_rent3_dre.sql
-- RENT3 — Demonstração de Resultado (DRE)

select
    "DT_REFER"      as data_referencia,
    "DT_FIM_EXERC"  as data_fim_exercicio,
    "CD_CONTA"      as codigo_conta,
    "DS_CONTA"      as descricao_conta,
    "VL_CONTA"      as valor,
    "ESCALA_MOEDA"  as escala,
    _extracted_at
from {{ ref('stg_cvm') }}
where "CNPJ_CIA" = '16670085000155'
  and "CD_CONTA" like '3.%'
order by "DT_REFER" desc, "CD_CONTA"

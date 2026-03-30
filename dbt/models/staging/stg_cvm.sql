{{
    config(
        materialized = "incremental",
        incremental_strategy = "append",
        alias = "stg_cvm"
    )
}}

-- stg_cvm.sql
-- Normalizes raw CVM data (income statement, balance sheet, cash flow):
-- casts types and renames columns to English.
-- Incremental: only processes rows extracted after the latest loaded timestamp.

select
    "CNPJ_CIA"                          as cnpj,
    "DENOM_CIA"                         as company_name,
    "CD_CVM"                            as cvm_code,
    "DT_REFER"::date                    as ref_date,
    "VERSAO"                            as version,
    "GRUPO_DFP"                         as report_group,
    "MOEDA"                             as currency,
    "ESCALA_MOEDA"                      as currency_scale,
    "ORDEM_EXERC"                       as exercise_order,
    "DT_INI_EXERC"::date                as period_start,
    "DT_FIM_EXERC"::date                as period_end,
    "CD_CONTA"                          as account_code,
    "DS_CONTA"                          as account_name,
    CAST(REPLACE(CAST("VL_CONTA" AS VARCHAR), ',', '.') AS NUMERIC(18,2)) as account_value,
    "ST_CONTA_FIXA"                     as fixed_account,
    _extracted_at
from {{ source('staging', 'raw_cvm') }}
where "CNPJ_CIA" is not null

{% if is_incremental() %}
    and _extracted_at > (
        select coalesce(max(_extracted_at), '1900-01-01'::timestamptz)
        from {{ this }}
    )
{% endif %}

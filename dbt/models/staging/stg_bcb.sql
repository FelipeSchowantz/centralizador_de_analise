{{
    config(
        materialized = "incremental",
        incremental_strategy = "append",
        alias = "stg_bcb"
    )
}}

-- stg_bcb.sql
-- Normalizes raw BCB macro data: casts types and renames columns to English.
-- NaN strings (from pandas) are converted to NULL before numeric casting.
-- Incremental: only processes rows extracted after the latest loaded timestamp.

select
    data::date                                              as ref_date,
    NULLIF(selic_meta,       'NaN')::numeric                as selic_rate,
    NULLIF(ipca_mensal,      'NaN')::numeric                as ipca_monthly,
    NULLIF(desemprego,       'NaN')::numeric                as unemployment_rate,
    NULLIF(cambio_usd_brl,   'NaN')::numeric                as usd_brl_rate,
    NULLIF(balanco_comercial,'NaN')::numeric                as trade_balance,
    _extracted_at
from {{ source('staging', 'raw_bcb') }}
where data is not null

{% if is_incremental() %}
    and _extracted_at > (
        select coalesce(max(_extracted_at), '1900-01-01'::timestamptz)
        from {{ this }}
    )
{% endif %}

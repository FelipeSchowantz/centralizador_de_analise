-- stg_yfinance.sql
-- Silver layer — Yahoo Finance
-- Tipagem e limpeza de formatação. Mesmas colunas da raw.

with source as (
    select * from {{ source('staging', 'raw_yfinance') }}
),

typed as (
    select
        -- VARCHAR
        cast(ticker              as varchar)   as ticker,
        cast("shortName"         as varchar)   as "shortName",
        cast(sector              as varchar)   as sector,

        -- FLOAT
        cast(replace(replace("marketCap",            '.', ''), ',', '.') as float)  as "marketCap",
        cast(replace(replace("currentPrice",         '.', ''), ',', '.') as float)  as "currentPrice",
        cast(replace(replace("trailingPE",           '.', ''), ',', '.') as float)  as "trailingPE",
        cast(replace(replace("priceToBook",          '.', ''), ',', '.') as float)  as "priceToBook",
        cast(replace(replace("enterpriseToEbitda",   '.', ''), ',', '.') as float)  as "enterpriseToEbitda",
        cast(replace(replace("returnOnEquity",       '.', ''), ',', '.') as float)  as "returnOnEquity",
        cast(replace(replace("profitMargins",        '.', ''), ',', '.') as float)  as "profitMargins",
        cast(replace(replace("ebitdaMargins",        '.', ''), ',', '.') as float)  as "ebitdaMargins",
        cast(replace(replace("dividendYield",        '.', ''), ',', '.') as float)  as "dividendYield",
        cast(replace(replace("debtToEquity",         '.', ''), ',', '.') as float)  as "debtToEquity",
        cast(replace(replace("totalRevenue",         '.', ''), ',', '.') as float)  as "totalRevenue",
        cast(replace(replace("netIncomeToCommon",    '.', ''), ',', '.') as float)  as "netIncomeToCommon",

        -- TIMESTAMPTZ
        cast(_extracted_at as timestamptz)    as _extracted_at

    from source
)

select * from typed

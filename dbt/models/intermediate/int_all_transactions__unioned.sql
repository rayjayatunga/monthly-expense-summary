{{
    config(
        materialized='view'
    )
}}

-- Union all transaction sources into a single table
-- Only keep common columns across all sources

with amex as (
    select
        transaction_date,
        description,
        merchant_name,
        amount,
        account_type,
        source
    from {{ ref('base_amex__transactions') }}
),

scotia_credit as (
    select
        transaction_date,
        description,
        merchant_name,
        amount,
        account_type,
        source
    from {{ ref('base_scotia_credit__transactions') }}
),

scotia_chequing as (
    select
        transaction_date,
        description,
        merchant_name,
        amount,
        account_type,
        source
    from {{ ref('base_scotia_chequing__transactions') }}
),

unioned as (
    select * from amex
    union all
    select * from scotia_credit
    union all
    select * from scotia_chequing
)

select * from unioned

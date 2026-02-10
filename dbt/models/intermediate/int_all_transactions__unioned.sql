{{
    config(
        materialized='view'
    )
}}

-- Union all transaction sources into a single table.
-- Only keep common columns across all sources.
-- Note: Scotia models will be added when data is available.

WITH amex AS (
    SELECT
        transaction_date,
        description,
        merchant_name,
        amount,
        account_type,
        source
    FROM {{ ref('base_amex__transactions') }}
)

{#
TODO: Add Scotia models when data is uploaded:

, scotia_credit AS (
    SELECT
        transaction_date,
        description,
        merchant_name,
        amount,
        account_type,
        source
    FROM {{ ref('base_scotia_credit__transactions') }}
),

scotia_chequing AS (
    SELECT
        transaction_date,
        description,
        merchant_name,
        amount,
        account_type,
        source
    FROM {{ ref('base_scotia_chequing__transactions') }}
),

combined AS (
    SELECT * FROM amex
    UNION ALL
    SELECT * FROM scotia_credit
    UNION ALL
    SELECT * FROM scotia_chequing
)

SELECT * FROM combined
#}

-- For now, just Amex
SELECT * FROM amex

{{
    config(
        materialized='view'
    )
}}

-- TODO: Update this model once we have the actual Scotia credit card CSV format.
-- This is a placeholder structure based on common bank CSV formats.

WITH source AS (
    SELECT * FROM {{ source('raw', 'scotia_credit_transactions') }}
),

renamed AS (
    SELECT
        -- Transaction details
        -- TODO: Replace column names with actual Scotia CSV columns
        CAST(transaction_date AS DATE) AS transaction_date,
        description,
        merchant AS merchant_name,
        CAST(amount AS NUMERIC) AS amount,

        -- Account classification
        'credit_card' AS account_type,

        -- Ingestion metadata
        source,
        uploaded_at,
        file_name,
        processing_date

    FROM source
)

SELECT * FROM renamed

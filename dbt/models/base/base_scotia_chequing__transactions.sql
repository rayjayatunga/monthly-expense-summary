{{
    config(
        materialized='view'
    )
}}

-- TODO: Update this model once we have the actual Scotia chequing CSV format.
-- This is a placeholder structure based on common bank CSV formats.

WITH source AS (
    SELECT * FROM {{ source('raw', 'scotia_chequing_transactions') }}
),

renamed AS (
    SELECT
        -- Transaction details
        -- TODO: Replace column names with actual Scotia CSV columns
        CAST(transaction_date AS DATE) AS transaction_date,
        description,
        payee AS merchant_name,
        CAST(amount AS NUMERIC) AS amount,

        -- Account classification
        'chequing' AS account_type,

        -- Ingestion metadata
        source,
        uploaded_at,
        file_name,
        processing_date

    FROM source
)

SELECT * FROM renamed

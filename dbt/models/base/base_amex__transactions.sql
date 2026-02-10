{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT * FROM {{ source('raw', 'amex_transactions') }}
),

/*
    Deduplicate before any transformation.

    When a broader date range is downloaded (e.g. start-of-year), previously
    loaded transactions will be re-uploaded. The raw table is append-only, so
    we deduplicate here in the base layer using the SHA-256 transaction_hash
    that was stamped by the Python ingestion script.

    We keep the LATEST upload of each hash (highest uploaded_at) so that any
    manual corrections to the source file are always reflected.
*/
deduplicated AS (
    SELECT *
    FROM source
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY transaction_hash
        ORDER BY uploaded_at DESC
    ) = 1
),

renamed AS (
    SELECT
        -- Dates
        PARSE_DATE('%d %b. %Y', Date) AS transaction_date,
        PARSE_DATE('%d %b. %Y', Date_Processed) AS transaction_processed_on,

        -- Transaction details
        Description AS description,
        Cardmember AS cardmember,
        Merchant AS merchant_name,
        Merchant_Address AS merchant_address,

        -- Monetary fields
        -- Python already strips '$' / ',' so these arrive as FLOAT64.
        -- We cast to NUMERIC for exact decimal arithmetic.
        CAST(Amount AS NUMERIC) AS amount,
        CAST(Foreign_Spend_Amount AS NUMERIC) AS foreign_amount,

        -- Foreign_Currency is pre-extracted by the Python ingestion script
        -- before the numeric cleaning strips the code from the amount string.
        Foreign_Currency AS foreign_currency,

        CAST(Commission AS NUMERIC) AS commission,
        CAST(Exchange_Rate AS NUMERIC) AS exchange_rate,

        CASE
            WHEN Foreign_Spend_Amount IS NOT NULL
                AND CAST(Foreign_Spend_Amount AS NUMERIC) != 0
            THEN TRUE
            ELSE FALSE
        END AS is_foreign_transaction,

        -- Supplementary info
        Additional_Information AS additional_info,

        -- Account classification
        'credit_card' AS account_type,

        -- Deduplication key (SHA-256 of date|description|amount|cardmember)
        transaction_hash,

        -- Ingestion metadata
        source,
        uploaded_at,
        file_name,
        processing_date

    FROM deduplicated
)

SELECT * FROM renamed

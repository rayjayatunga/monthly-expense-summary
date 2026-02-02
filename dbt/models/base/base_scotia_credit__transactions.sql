{{
    config(
        materialized='view'
    )
}}

-- TODO: Update this model once we have actual Scotia credit card CSV format
-- This is a placeholder structure based on common bank CSV formats

with source as (
    select * from {{ source('raw', 'scotia_credit_transactions') }}
),

renamed as (
    select
        -- Transaction details
        -- TODO: Replace column names with actual Scotia CSV columns
        cast(transaction_date as date) as transaction_date,
        description,
        merchant as merchant_name,
        cast(amount as numeric) as amount,
        
        -- Account classification
        'credit_card' as account_type,
        
        -- Metadata
        source,
        uploaded_at,
        file_name,
        processing_date
        
    from source
)

select * from renamed

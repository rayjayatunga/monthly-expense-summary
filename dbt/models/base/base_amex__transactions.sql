{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('raw', 'amex_transactions') }}
),

renamed as (
    select
        -- Transaction details
        cast(Date as date) as transaction_date,
        cast(Date_Processed as date) as transaction_date_processed,
        Description as description,
        Merchant as merchant_name,
        cast(Amount as numeric) as amount,
        
        -- Foreign transaction details
        cast(Foreign_Spend_Amount as numeric) as foreign_amount,
        cast(Commission as numeric) as commission,
        cast(Exchange_Rate as numeric) as exchange_rate,
        case 
            when Foreign_Spend_Amount is not null and Foreign_Spend_Amount != 0 
            then true 
            else false 
        end as is_foreign_transaction,
        
        -- Additional info
        Additional_Information as additional_info,
        Address as address,
        City___Province as city_province,
        Postal_Code as postal_code,
        Country as country,
        Reference as reference,
        
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

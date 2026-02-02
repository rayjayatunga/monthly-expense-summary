{{
    config(
        materialized='table'
    )
}}

with transactions as (
    select * from {{ ref('int_all_transactions__unioned') }}
),

-- Weekly aggregations
weekly as (
    select
        'week' as period_type,
        date_trunc(transaction_date, week) as period_start_date,
        date_add(date_trunc(transaction_date, week), interval 6 day) as period_end_date,
        sum(abs(amount)) as total_expenses,
        count(*) as transaction_count,
        avg(abs(amount)) as avg_transaction_amount,
        count(distinct source) as source_count
    from transactions
    where amount < 0  -- Only expenses (negative amounts)
    group by 1, 2, 3
),

-- Monthly aggregations
monthly as (
    select
        'month' as period_type,
        date_trunc(transaction_date, month) as period_start_date,
        last_day(date_trunc(transaction_date, month)) as period_end_date,
        sum(abs(amount)) as total_expenses,
        count(*) as transaction_count,
        avg(abs(amount)) as avg_transaction_amount,
        count(distinct source) as source_count
    from transactions
    where amount < 0
    group by 1, 2, 3
),

-- Yearly aggregations
yearly as (
    select
        'year' as period_type,
        date_trunc(transaction_date, year) as period_start_date,
        date(date_trunc(transaction_date, year) + interval 1 year - interval 1 day) as period_end_date,
        sum(abs(amount)) as total_expenses,
        count(*) as transaction_count,
        avg(abs(amount)) as avg_transaction_amount,
        count(distinct source) as source_count
    from transactions
    where amount < 0
    group by 1, 2, 3
),

combined as (
    select * from weekly
    union all
    select * from monthly
    union all
    select * from yearly
)

select * from combined
order by period_start_date desc, period_type

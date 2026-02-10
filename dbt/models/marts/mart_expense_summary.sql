{{
    config(
        materialized='table'
    )
}}

WITH transactions AS (
    SELECT * FROM {{ ref('int_all_transactions__unioned') }}
),

-- Weekly aggregations
weekly AS (
    SELECT
        'week' AS period_type,
        DATE_TRUNC(transaction_date, WEEK) AS period_start_date,
        DATE_ADD(DATE_TRUNC(transaction_date, WEEK), INTERVAL 6 DAY) AS period_end_date,
        SUM(ABS(amount)) AS total_expenses,
        COUNT(*) AS transaction_count,
        AVG(ABS(amount)) AS avg_transaction_amount
    FROM transactions
    WHERE amount < 0  -- Only expenses (negative amounts)
    GROUP BY 1, 2, 3
),

-- Monthly aggregations
monthly AS (
    SELECT
        'month' AS period_type,
        DATE_TRUNC(transaction_date, MONTH) AS period_start_date,
        LAST_DAY(DATE_TRUNC(transaction_date, MONTH)) AS period_end_date,
        SUM(ABS(amount)) AS total_expenses,
        COUNT(*) AS transaction_count,
        AVG(ABS(amount)) AS avg_transaction_amount
    FROM transactions
    WHERE amount < 0
    GROUP BY 1, 2, 3
),

-- Yearly aggregations
yearly AS (
    SELECT
        'year' AS period_type,
        DATE_TRUNC(transaction_date, YEAR) AS period_start_date,
        DATE(DATE_TRUNC(transaction_date, YEAR) + INTERVAL 1 YEAR - INTERVAL 1 DAY) AS period_end_date,
        SUM(ABS(amount)) AS total_expenses,
        COUNT(*) AS transaction_count,
        AVG(ABS(amount)) AS avg_transaction_amount
    FROM transactions
    WHERE amount < 0
    GROUP BY 1, 2, 3
),

combined AS (
    SELECT * FROM weekly
    UNION ALL
    SELECT * FROM monthly
    UNION ALL
    SELECT * FROM yearly
)

SELECT * FROM combined
ORDER BY period_start_date DESC, period_type

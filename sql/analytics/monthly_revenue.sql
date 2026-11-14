CREATE OR REPLACE VIEW monthly_revenue AS
    SELECT
        DATE_TRUNC('month', invoice_date)::date AS revenue_month,
        ROUND(SUM(quantity * unit_price), 2)    AS revenue,
        COUNT(DISTINCT customer_id)             AS customer_count,
        COUNT(DISTINCT invoice_no)              AS order_count,
        SUM(quantity)                           AS units_sold
    FROM
        transactions
    WHERE
        quantity > 0
    GROUP BY
        revenue_month;

COMMENT ON VIEW monthly_revenue IS
    'Gross sales per month. Excludes returns.';
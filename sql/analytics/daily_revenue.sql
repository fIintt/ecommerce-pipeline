CREATE OR REPLACE VIEW daily_revenue AS
    SELECT
        invoice_date::date                      AS revenue_date,
        ROUND(SUM(quantity * unit_price), 2)    AS revenue,
        COUNT(DISTINCT customer_id)             AS customer_count,
        COUNT(DISTINCT invoice_no)              AS order_count,
        SUM(quantity)                           AS units_sold
    FROM
        transactions
    WHERE
        quantity > 0
    GROUP BY
        invoice_date::date;

COMMENT ON VIEW daily_revenue IS
    'Gross sales per day. Excludes returns.';
CREATE OR REPLACE VIEW revenue_by_country AS
    WITH country_revenue AS (
        SELECT
            country,
            SUM(quantity * unit_price)    AS revenue,
            COUNT(DISTINCT customer_id)   AS customer_count,
            COUNT(DISTINCT invoice_no)    AS order_count,
            SUM(quantity)                 AS units_sold
        FROM
            transactions
        WHERE
            quantity > 0
        GROUP BY
            country
    )

    SELECT
        country,
        ROUND(revenue, 2)                                  AS revenue,
        customer_count,
        order_count,
        units_sold,
        ROUND(revenue * 100.0 / SUM(revenue) OVER (), 2)   AS revenue_share_pct
    FROM 
        country_revenue;
    
    
COMMENT ON VIEW revenue_by_country IS
    'Gross sales per country. Excludes returns.';

COMMENT ON COLUMN revenue_by_country.customer_count IS
    'Anonymous customers are not counted.';
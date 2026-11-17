CREATE OR REPLACE VIEW non_product_summary AS
    SELECT
        UPPER(stock_code)                          AS stock_code,
        MODE() WITHIN GROUP (ORDER BY description) AS typical_description,
        COUNT(*)                                   AS line_count,
        ROUND(SUM(quantity * unit_price), 2)       AS net_value
    FROM
        transactions
    WHERE
        NOT _is_product
    GROUP BY
        UPPER(stock_code);

COMMENT ON VIEW non_product_summary IS
    'Non-product transactions.';
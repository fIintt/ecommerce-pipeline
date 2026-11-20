CREATE OR REPLACE VIEW non_product_summary AS
    SELECT
        UPPER(stock_code)                          AS stock_code,
        MODE() WITHIN GROUP (ORDER BY description) AS typical_description,
        COUNT(*)                                   AS line_count,
        ROUND(SUM(quantity * unit_price), 2)       AS net_value
    FROM
        transactions
    WHERE
        stock_code !~ '^[0-9]{5}'
    GROUP BY
        UPPER(stock_code);

COMMENT ON VIEW non_product_summary IS
    'Lines whose stock code is not a catalog code (postage, fees, discounts, manual entries, samples), per stock code: line count and net value.';
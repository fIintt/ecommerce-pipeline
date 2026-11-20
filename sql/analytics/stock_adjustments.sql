CREATE OR REPLACE VIEW stock_adjustments AS
    SELECT
        COALESCE(UPPER(description), '(no reason)')             AS reason,
        COUNT(*)                                                AS count,
        COALESCE(SUM(quantity) FILTER (WHERE quantity > 0), 0)  AS units_added,
        COALESCE(SUM(quantity) FILTER (WHERE quantity < 0), 0)  AS units_removed
    FROM
        transactions
    WHERE
        stock_code ~ '^[0-9]{5}'
        AND unit_price = 0
        AND customer_id IS NULL
    GROUP BY
        UPPER(description);

COMMENT ON VIEW stock_adjustments IS
    'Zero-price, customer-less lines on catalog codes: inventory write-offs, found stock and channel transfers, grouped by the free-text reason.';
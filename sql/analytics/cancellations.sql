CREATE OR REPLACE VIEW cancellations AS
    SELECT
        invoice_no,
        invoice_date::date             AS cancel_date,
        customer_id,
        country,
        stock_code,
        description,
        ABS(quantity)                  AS quantity_returned,
        ABS(quantity) * unit_price     AS value_returned
    FROM
        transactions
    WHERE 
        invoice_no LIKE 'C%';

COMMENT ON VIEW cancellations IS
    'Cancelled/returned invoice lines (C-prefixed invoices) with positive quantity and value. Excludes stock adjustments.';
CREATE OR REPLACE VIEW rfm AS
    WITH rfm AS (
        SELECT customer_id,
            (SELECT MAX(invoice_date::date) FROM transactions) - MAX(invoice_date::date) AS recency,
            COUNT(DISTINCT invoice_no)                                                   AS frequency,
            SUM(quantity * unit_price)                                                   AS monetary
        FROM 
            transactions
        WHERE 
            customer_id IS NOT NULL
        GROUP BY 
            customer_id
    )
    SELECT 
        customer_id,
        NTILE(5) OVER (ORDER BY recency DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency)    AS f_score,
        NTILE(5) OVER (ORDER BY monetary)     AS m_score
    FROM 
        rfm;

COMMENT ON VIEW rfm IS
    'Customer RFM (Recency, Frequency, Monetary) metrics and quintile scores (1-5). Excludes null customer_ids.';
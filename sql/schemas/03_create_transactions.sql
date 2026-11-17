CREATE TABLE IF NOT EXISTS transactions (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_no          TEXT NOT NULL,
    stock_code          TEXT NOT NULL,
    description         TEXT,
    quantity            INT NOT NULL CHECK (quantity <> 0),
    invoice_date        TIMESTAMP NOT NULL,
    unit_price          NUMERIC(12,4) NOT NULL CHECK (unit_price >= 0),
    customer_id         BIGINT,
    country             TEXT,
    _loaded_file_id     INT NOT NULL REFERENCES loaded_files(id) ON DELETE RESTRICT,
    _source_row_number  BIGINT NOT NULL,
    _is_product         BOOLEAN GENERATED ALWAYS AS (stock_code ~ '^[0-9]{5}') STORED, -- STORED calculates the value when the row is written (the alternative is VIRTUAL)

    UNIQUE (_loaded_file_id, _source_row_number)
);

CREATE INDEX IF NOT EXISTS idx_customer_id      ON transactions (customer_id);
CREATE INDEX IF NOT EXISTS idx_invoice_no       ON transactions (invoice_no);
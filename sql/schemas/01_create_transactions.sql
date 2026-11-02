CREATE TABLE IF NOT EXISTS transactions (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_file_hash    TEXT NOT NULL,
    source_row_number   BIGINT NOT NULL,
    invoice_no          TEXT NOT NULL,
    stock_code          TEXT NOT NULL,
    description         TEXT,
    quantity            INT NOT NULL,
    invoice_date        TIMESTAMP NOT NULL,
    unit_price          NUMERIC(12,4) NOT NULL,
    customer_id         BIGINT,
    country             TEXT,

    CONSTRAINT uq_transactions_source_record
        UNIQUE (source_file_hash, source_row_number)
);
CREATE TABLE transactions (
  id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  invoice_no   TEXT NOT NULL,
  stock_code   TEXT NOT NULL,
  description  TEXT,
  quantity     INT NOT NULL,
  invoice_date TIMESTAMP NOT NULL,
  unit_price   NUMERIC(12,4) NOT NULL,
  customer_id  BIGINT,
  country      TEXT
);
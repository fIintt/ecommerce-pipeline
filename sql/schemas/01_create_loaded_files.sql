CREATE TABLE IF NOT EXISTS loaded_files (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    file_hash       TEXT NOT NULL UNIQUE,
    file_name       TEXT NOT NULL,
    row_count       INT,
    loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
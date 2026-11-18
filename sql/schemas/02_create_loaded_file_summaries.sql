CREATE TABLE IF NOT EXISTS loaded_file_summaries (
    id                  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    loaded_file_id      INT NOT NULL REFERENCES loaded_files(id) ON DELETE RESTRICT, 
    row_count           BIGINT NOT NULL,
    rejected_count      BIGINT NOT NULL,
    skipped_count       BIGINT NOT NULL,
    loaded_count        BIGINT NOT NULL,
    elapsed_seconds     NUMERIC(10, 2) NOT NULL,
    loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (row_count = rejected_count + skipped_count + loaded_count)
);
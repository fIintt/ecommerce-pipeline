## Use Polars (not Spark) to process the CSV

**Decision:** The pipeline reads and transforms the CSV with Polars on a single machine. PySpark is not used.

**Why:**

- The dataset is small (about 40 MB), so it fits in memory with room to spare.
- Polars' lazy API lets validation and transformation run as one optimized query.
- Spark adds a cluster or JVM setup and more moving parts, with no benefit at this size.

**Consequences:**

- The pipeline is limited to what one machine's memory can handle.
- It's simple to run and test locally: no cluster, and tests run in seconds.

**Revisit if:** the input grows to a size that no longer fits comfortably in memory (for example, multiple GB per file), or the load time becomes a problem. At that point, try Polars streaming mode first before considering Spark.

## Exact duplicate rows are loaded, not dropped

**Decision:** Rows that are identical across all business columns are kept and loaded. Each one gets its own surrogate `id`.

**Why:**

- The source has no line number or transaction ID, so a real repeated line item (same product scanned 4 times) can't be told apart from an export error.
- Dropping rows silently loses data that can't be recovered. Deduplicating later in SQL is easy.
- Re-running the same file is already prevented by `loaded_files`, so row-level dedup isn't needed for idempotency.

**Consequences:**

- If some duplicates are export errors, quantity and revenue totals will be overstated.
- The run summary reports them as `dup_rows` (informational only; they are included in `loaded`). Reconciliation is `read = rejected + skipped + loaded`.
- Anyone who needs deduplicated data should do it in a query or view.

## Lineage and integrity

**Decision:** Every row in `transactions` records the file and CSV row it came from,
and PostgreSQL enforces basic data validity itself.

### Schema

- `_loaded_file_id INT NOT NULL REFERENCES loaded_files(id)`: the file the row was loaded from.
- `_source_row_number BIGINT NOT NULL`: the row's position in the source CSV.
- `CHECK (quantity <> 0)` and `CHECK (unit_price >= 0)`.
- `UNIQUE (_loaded_file_id, _source_row_number)`.

### Why

- **Traceability:** any row can be traced to its file (via `loaded_files`) and its line in the CSV. Needed because exact duplicate rows are kept (see N1), so business columns alone can't identify a row, and the surrogate `id` carries no source meaning.
- **Integrity in the database:** the unique pair stops the same source line being stored twice for a file; the FK prevents orphaned rows and deleting a file record that still has transactions; the CHECKs reject invalid values even if validation has a bug.
- **Complements `file_hash`:** the hash prevents loading the same file twice (pipeline level). The new constraints protect the table itself and can't catch a different file with identical content.
- **Targeted cleanup:** one bad load can be removed with `DELETE FROM transactions WHERE _loaded_file_id = <id>`.

### Conventions

- `_source_row_number` counts **data rows starting at 1** (the header is not counted).
- It is assigned in `extract_csv` **before** any validation or filtering, so numbers stay stable and rejected rows keep their original position. Rejected rows (Parquet) carry it too.
- `transactions` is **append-only**: corrections arrive as new rows, not updates, so lineage never goes stale.
- The CHECK constraints are a **second line of defense**. Validation should already reject these rows, so a constraint violation indicates a pipeline bug and aborts the load.

### Verification

- End-to-end run on a fresh database: loads without errors.
- Lineage spot-check: a row's `(loaded_file_id, source_row_number)` matched the expected CSV line.
- Manual inserts violating each constraint (quantity = 0, negative price, duplicate pair, nonexistent file id) were all rejected.

### Known limits

- The unique pair doesn't prevent the same content being loaded under a different file id; `file_hash` covers that case.
- `_source_row_number` counts parsed rows, not physical lines, so it can drift from line numbers if a quoted field contains a line break.

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

## Indexing

I picked indexes by starting from the queries I expect to run, then checking each plan with `EXPLAIN (ANALYZE)`. I first tested four candidate indexes, then kept only the two tied to queries I actually run.

Dataset: 541,907 loaded rows, local PostgreSQL. "Before" means no secondary indexes (only the PK and the `UNIQUE (_loaded_file_id, _source_row_number)` constraint, which always exist).

### Benchmark queries

| #   | Query                                                            | Purpose                       |
| --- | ---------------------------------------------------------------- | ----------------------------- |
| Q1  | `WHERE customer_id = 14601`                                      | all purchases of one customer |
| Q2  | `WHERE invoice_no = '542800'`                                    | all lines of one invoice      |
| Q3  | `WHERE invoice_date` in a 1-month range, grouped by day          | daily revenue                 |
| Q4  | `WHERE stock_code = '22510' AND invoice_date` in a 1-month range | one product's sales over time |
| Q5  | `GROUP BY customer_id ORDER BY total DESC LIMIT 10`              | top customers by spend        |

### Final indexes

```sql
CREATE INDEX IF NOT EXISTS idx_customer_id ON transactions (customer_id);
CREATE INDEX IF NOT EXISTS idx_invoice_no  ON transactions (invoice_no);
```

| Index           | Serves | Why                                                                             |
| --------------- | ------ | ------------------------------------------------------------------------------- |
| `(customer_id)` | Q1     | Selective equality filter: a customer has few rows compared to the whole table. |
| `(invoice_no)`  | Q2     | An invoice has only a handful of line items, so a lookup returns very few rows. |

### Results

All times are medians. "With index" for Q3 and Q4 was measured while those indexes existed; they were dropped afterwards (see below), so those two queries now run as sequential scans again.

| Query | Before (ms) | With index (ms) | Plan change           | Index kept? |
| ----- | ----------- | --------------- | --------------------- | ----------- |
| Q1    | 41.910      | 0.050           | Seq Scan → Index Scan | yes         |
| Q2    | 52.091      | 0.047           | Seq Scan → Index Scan | yes         |
| Q3    | 52.064      | 4.504           | Seq Scan → Index Scan | dropped     |
| Q4    | 48.078      | 0.053           | Seq Scan → Index Scan | dropped     |
| Q5    | 80.791      | n/a             | unchanged             | no index    |

- **Q5** stays a Seq Scan. It has no `WHERE` clause, so every row must be read to compute the sums. An index cannot skip rows that have to be read anyway, and `ORDER BY total` sorts a computed value that no index covers.
- **Q3** improved less (about 11x) than the lookups, because a one-month range covers a large slice of the table, so many more rows are read.
- **Q4** was served by an index on `stock_code`. The date filter is applied to the few rows it returns, so the date didn't need to be in the index.

### Cost of indexing

| Execution      | No secondary indexes (unlogged test table) | 4 candidate indexes | Final 2 indexes |
| -------------- | ------------------------------------------ | ------------------- | --------------- |
| COPY load time | 1.76s                                      | 10.6s               | 7.59s           |

The 1.76s baseline used an `UNLOGGED` table, which skips WAL writes, so part of the gap is not caused by indexes alone.

| Index                        | Size (MB) | Status  |
| ---------------------------- | --------- | ------- |
| `(customer_id)`              | 4.56      | kept    |
| `(invoice_no)`               | 4.10      | kept    |
| `(invoice_date)`             | 7.22      | dropped |
| `(stock_code, invoice_date)` | 16        | dropped |

Index sizes come from `SELECT pg_size_pretty(pg_relation_size('index_name'));`.

### Why I dropped two indexes

`stock_code` and `(stock_code, invoice_date)` are rarely queried in this project, and the composite was the largest index (16 MB). `invoice_date` helped Q3 but I don't run date-range queries often enough to justify its 7.22 MB and the extra load time. If a product or date-range query becomes common, the index is a one-line `CREATE INDEX` and builds in a second or two on this table.

### Takeaway

Indexes help queries that select a small part of the table (Q1, Q2, Q4) and do nothing for queries that scan everything (Q5). Each index costs disk space and write speed, so I kept only the ones for queries I actually run.

## Notes

- Records with negative quantities and "C" in `invoice_no` are cancellations.
- Records with negative quantities and without "C" in `invoice_no` are damaged/lost/unsure, etc.
- 541,909 rows were read and 541,907 loaded; 2 rows were rejected by validation. TODO: say why.
- TODO: say whether cancellations are excluded from revenue or kept as negatives.

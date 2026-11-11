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
[Dataset](https://www.kaggle.com/datasets/carrie1/ecommerce-data)

## Indexing

I picked indexes by starting from the queries I expect to run, then checking each plan with `EXPLAIN (ANALYZE)`.

### Benchmark queries

| # | Query | Purpose |
|---|---|---|
| Q1 | `WHERE customer_id = ...` | all purchases of one customer |
| Q2 | `WHERE invoice_no = ...` | all lines of one invoice |
| Q3 | `WHERE invoice_date` in a 1-month range, grouped by day | daily revenue |
| Q4 | `WHERE stock_code = ... AND invoice_date` in a 3-month range | one product's sales over time |
| Q5 | `GROUP BY customer_id ORDER BY total DESC LIMIT 10` | top customers by spend |

### Indexes and why they exist

| Index | Serves | Why |
|---|---|---|
| `(customer_id)` | Q1 | Selective equality filter: a customer has few rows compared to the whole table. |
| `(invoice_no)` | Q2 | An invoice has only a handful of line items, so a lookup returns very few rows. |
| `(invoice_date)` | Q3 | Range filter on dates. Also useful for any date-only query. |
| `(stock_code, invoice_date)` | Q4 | Equality on `stock_code` first, then a range on `invoice_date`. Column order matters: the index is sorted by product, then by date within each product. |

### Results

Before and After results are medians

| Query | Before (ms) | After (ms) | Plan change |
|-------|------|---|---|
| Q1    | 44.335 | 0.094 | Seq Scan → Index Scan |
| Q2    | 51.06 | 0.0575 | Seq Scan → Index Scan |
| Q3    | ... | ... | Seq Scan → ... |
| Q4    | ... | ... | Seq Scan → ... |
| Q5    | ... | ... | unchanged |

### What did not improve, and why

- **Q5** stays a Seq Scan. It has no `WHERE` clause, so every row must be read to compute the sums. An index cannot skip rows that have to be read anyway, and `ORDER BY total` sorts a computed value that no index covers.

### Cost of indexing

| Execution       | Without indexes | With indexes |
|-----------------|-----------------|--------------|
| COPY load time  |           9.55s |        0.30s |

| Index           | Size |
|-----------------|---|
| `(customer_id)` | ... |
| `(invoice_no)` | ... |
| `(invoice_date)` | ... |
| `(stock_code, invoice_date)` | ... |

Index sizes come from `SELECT pg_size_pretty(pg_relation_size('index_name'));`.

### Takeaway

Indexes help queries that select a small part of the table (Q1, Q2, Q4) and do nothing for queries that scan everything (Q5). Each index costs disk space and write speed, so I only kept the ones tied to a measured improvement.
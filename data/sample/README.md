# Sample transaction data

`sample.csv` is a synthetic 49-row stand-in for the real e-commerce dataset. It exercises successful catalog sales, cancellations, non-product lines, stock adjustments, a free item, and eight rejected input/output validation cases.

The file uses cp1252 encoding and `M/D/YYYY H:MM` dates. Run it from the repository root:

```bash
uv run pipeline --path data/sample/sample.csv
```

On a fresh database, the run should report `49` read, `8` rejected, `0` skipped, and `41` loaded. The complete fixture description and expected database checks are in the repository [README](../../README.md).

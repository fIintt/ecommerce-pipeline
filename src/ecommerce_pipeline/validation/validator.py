import polars as pl


def is_blank(col: str) -> pl.Expr:
    return pl.col(col).is_null() | (pl.col(col).str.strip_chars() == "")


def _apply_rules(
    lf: pl.LazyFrame, rules: dict[str, pl.Expr]
) -> tuple[pl.LazyFrame, pl.LazyFrame]:
    flagged = lf.with_columns(
        pl.concat_str(
            [
                pl.when(expr.fill_null(False)).then(pl.lit(name))
                for name, expr in rules.items()
            ],
            separator=";",
            ignore_nulls=True,
        ).alias("reject_reason")
    )

    valid = flagged.filter(pl.col("reject_reason") == "").drop("reject_reason")
    rejected = flagged.filter(pl.col("reject_reason") != "")

    return valid, rejected


def validate_input(
    lf: pl.LazyFrame, required_cols: list[str], input_rules: dict[str, pl.Expr]
) -> tuple[pl.LazyFrame, pl.LazyFrame]:
    missing = [col for col in required_cols if col not in lf.collect_schema().names()]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return _apply_rules(lf, input_rules)


def validate_output(
    lf: pl.LazyFrame, output_rules: dict[str, pl.Expr]
) -> tuple[pl.LazyFrame, pl.LazyFrame]:
    return _apply_rules(lf, output_rules)

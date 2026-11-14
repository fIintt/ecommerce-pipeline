import hashlib
from pathlib import Path

import polars as pl

from ecommerce_pipeline.ingestion.extractor import extract_csv, hash_file


def test_extract_csv_decodes_cp1252(tmp_path: Path):
    p = tmp_path / "t.csv"
    p.write_bytes("InvoiceNo,Description\n1,CAFÉ ÀU LAIT\n".encode("cp1252"))

    with extract_csv(p) as lf:
        df = lf.collect()

    assert df["Description"][0] == "CAFÉ ÀU LAIT"


def test_extract_csv_adds_source_row_number(tmp_path: Path):
    p = tmp_path / "t.csv"
    p.write_bytes(b"InvoiceNo\nA\nB\nC\n")

    with extract_csv(p) as lf:
        df = lf.collect()

    assert df["_source_row_number"].to_list() == [1, 2, 3]
    assert df.schema["_source_row_number"] == pl.Int64


def test_extract_csv_strips_header_whitespace(tmp_path: Path):
    p = tmp_path / "t.csv"
    p.write_bytes(b"  InvoiceNo  , Country \nA,UK\n")

    with extract_csv(p) as lf:
        df = lf.collect()

    assert df.columns[1:3] == ["InvoiceNo", "Country"]


def test_extract_csv_does_not_modify_source_dir(tmp_path: Path):
    p = tmp_path / "t.csv"
    p.write_bytes(b"InvoiceNo\nA\n")

    with extract_csv(p) as lf:
        lf.collect()

    assert list(tmp_path.iterdir()) == [p]


def test_hash_file_is_deterministic_and_content_based(tmp_path: Path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_bytes(b"same")
    b.write_bytes(b"same")

    assert hash_file(a) == hash_file(b)
    assert hash_file(a) == hashlib.sha256(b"same").hexdigest()

    b.write_bytes(b"different")

    assert hash_file(a) != hash_file(b)


def test_hash_file_handles_multiple_chunks(tmp_path: Path):
    p = tmp_path / "big.csv"
    p.write_bytes(b"x" * 25)

    assert hash_file(p, chunk_size=4) == hashlib.sha256(b"x" * 25).hexdigest()

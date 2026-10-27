"""Tests for dataset loader."""

import io
import pandas as pd
import pytest
from data_engine.loader import DatasetLoader

def test_load_sample_dataset():
    df, meta = DatasetLoader.load_sample_dataset()
    assert df is not None
    assert meta["success"] is True
    assert len(df) > 0
    assert "Revenue" in df.columns
    assert "Region" in df.columns

def test_load_csv_from_buffer():
    csv_data = "col1,col2,col2\n1,hello,world\n2,foo,bar\n"
    stream = io.BytesIO(csv_data.encode("utf-8"))
    df, meta = DatasetLoader.load_from_file(stream, "test.csv")
    assert df is not None
    assert meta["success"] is True
    assert len(df) == 2
    # Duplicate column should have been deduplicated
    assert len(df.columns) == 3
    assert len(set(df.columns)) == 3

def test_unsupported_file_extension():
    stream = io.BytesIO(b"data")
    df, meta = DatasetLoader.load_from_file(stream, "test.pdf")
    assert df is None
    assert meta["success"] is False
    assert "Unsupported file extension" in meta["error"]

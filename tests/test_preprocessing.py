"""Tests for data preprocessing operations."""

import pandas as pd
import pytest
from data_engine.preprocessing import PreprocessingEngine

def test_remove_duplicate_rows():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    new_df, metrics = PreprocessingEngine.remove_duplicate_rows(df)
    assert len(new_df) == 2
    assert metrics["removed_rows"] == 1
    assert len(df) == 3  # Original not mutated

def test_trim_whitespace():
    df = pd.DataFrame({"text": ["  hello ", "world  ", "clean"]})
    new_df, metrics = PreprocessingEngine.trim_whitespace(df, ["text"])
    assert list(new_df["text"]) == ["hello", "world", "clean"]
    assert metrics["cells_trimmed"] == 2

def test_impute_missing_numeric():
    df = pd.DataFrame({"vals": [10.0, None, 30.0]})
    new_df, metrics = PreprocessingEngine.impute_missing_numeric(df, "vals", strategy="mean")
    assert new_df["vals"].isna().sum() == 0
    assert new_df["vals"].iloc[1] == 20.0

def test_remove_outliers_iqr():
    df = pd.DataFrame({"vals": [10, 12, 11, 10, 12, 11, 500]})
    new_df, metrics = PreprocessingEngine.remove_outliers_iqr(df, "vals", factor=1.5)
    assert len(new_df) == 6
    assert 500 not in new_df["vals"].values
    assert metrics["outliers_removed"] == 1

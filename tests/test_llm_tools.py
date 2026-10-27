"""Tests for controlled LLM tools and deterministic fallback parser."""

import pandas as pd
import pytest
from llm.tool_executor import ToolExecutor
from llm.fallback import FallbackParser
from data_engine.profiler import DataProfiler
from data_engine.quality_score import QualityScoreCalculator

@pytest.fixture
def sample_dataset():
    df = pd.DataFrame({
        "Region": ["North", "South", "North", "West"],
        "Revenue": [100.0, 200.0, 300.0, 400.0],
        "Units": [10, 20, 30, 40]
    })
    profile = DataProfiler.profile_dataset(df)
    score = QualityScoreCalculator.calculate_score(profile)
    return df, profile, score

def test_tool_calculate_aggregation(sample_dataset):
    df, profile, score = sample_dataset
    res = ToolExecutor.execute_tool(
        "calculate_aggregation",
        {"group_by_column": "Region", "metric_column": "Revenue", "agg_func": "mean"},
        df, profile, score
    )
    assert res["success"] is True
    assert res["results"]["North"] == 200.0  # (100 + 300) / 2

def test_tool_calculate_correlation(sample_dataset):
    df, profile, score = sample_dataset
    res = ToolExecutor.execute_tool(
        "calculate_correlation",
        {"col1": "Revenue", "col2": "Units"},
        df, profile, score
    )
    assert res["success"] is True
    assert res["correlation"] == 1.0

def test_tool_invalid_column(sample_dataset):
    df, profile, score = sample_dataset
    res = ToolExecutor.execute_tool(
        "get_column_profile",
        {"column_name": "NonExistentColumn"},
        df, profile, score
    )
    assert res["success"] is False
    assert "not found" in res["error"]

def test_fallback_parser_summary(sample_dataset):
    df, profile, score = sample_dataset
    res = FallbackParser.answer_question("Give me a summary of this dataset", df, profile, score)
    assert res["success"] is True
    assert "Dataset Summary:" in res["answer"]
    assert res["tool"] == "get_dataset_summary"

def test_fallback_parser_aggregation(sample_dataset):
    df, profile, score = sample_dataset
    res = FallbackParser.answer_question("What is the average revenue by region?", df, profile, score)
    assert res["success"] is True
    assert res["tool"] == "calculate_aggregation"

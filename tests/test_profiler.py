"""Tests for data profiler and semantic type inference."""

import pandas as pd
import pytest
from data_engine.profiler import DataProfiler, SemanticType
from data_engine.quality_score import QualityScoreCalculator

def test_semantic_type_inference():
    df = pd.DataFrame({
        "order_id": ["ORD-1001", "ORD-1002", "ORD-1003", "ORD-1004"],
        "region": ["North", "South", "East", "West"],
        "revenue": [100.5, 250.0, 310.2, 450.0],
        "is_active": [True, False, True, False],
        "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
    })
    profile = DataProfiler.profile_dataset(df)
    cols = profile["columns"]
    
    assert cols["order_id"]["semantic_type"] == SemanticType.IDENTIFIER
    assert cols["region"]["semantic_type"] == SemanticType.CATEGORICAL
    assert cols["revenue"]["semantic_type"] == SemanticType.NUMERIC_CONTINUOUS
    assert cols["is_active"]["semantic_type"] == SemanticType.BOOLEAN
    assert cols["date"]["semantic_type"] == SemanticType.DATETIME

def test_issues_detection():
    df = pd.DataFrame({
        "id": ["1", "2", "2", "2"],
        "category": [" North ", "north", "NORTH", "NORTH"],
        "amount": [10.0, None, 1000.0, 1000.0]
    })
    profile = DataProfiler.profile_dataset(df)
    issues = profile["issues"]
    issue_types = [i["type"] for i in issues]
    
    assert "duplicate_rows" in issue_types
    assert "missing_values" in issue_types
    assert "whitespace" in issue_types
    assert "inconsistent_categories" in issue_types

def test_quality_score_calculation():
    # Pristine dataset should score near 100
    df_clean = pd.DataFrame({
        "id": ["1", "2", "3", "4", "5"],
        "val": [10.0, 20.0, 30.0, 40.0, 50.0]
    })
    prof_clean = DataProfiler.profile_dataset(df_clean)
    score_clean = QualityScoreCalculator.calculate_score(prof_clean)
    assert score_clean["overall_score"] >= 95.0
    assert score_clean["grade"] == "A"

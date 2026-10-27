"""Tests for visualization engine."""

import pandas as pd
import pytest
from data_engine.visualization import VisualizationEngine
from data_engine.profiler import DataProfiler

def test_recommended_charts():
    df = pd.DataFrame({
        "Region": ["North", "South", "East", "West"],
        "Revenue": [100.0, 200.0, 300.0, 400.0],
        "Units": [10, 20, 30, 40]
    })
    profile = DataProfiler.profile_dataset(df)
    charts = VisualizationEngine.generate_recommended_charts(df, profile)
    assert len(charts) > 0
    types = [c["type"] for c in charts]
    assert "heatmap" in types or "bar" in types or "histogram" in types

def test_custom_chart_builder():
    df = pd.DataFrame({
        "Category": ["A", "B", "A", "B"],
        "Score": [10, 20, 30, 40]
    })
    fig_bar = VisualizationEngine.build_custom_chart(df, "bar", "Category", "Score", agg_func="mean")
    assert fig_bar is not None

    fig_hist = VisualizationEngine.build_custom_chart(df, "histogram", "Score")
    assert fig_hist is not None

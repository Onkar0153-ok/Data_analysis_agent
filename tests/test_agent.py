"""Tests for Autonomous Agent workflow, planner, validation, and rollback."""

import pandas as pd
import pytest
from agent.planner import AgentPlanner
from agent.executor import AgentExecutor
from agent.validator import AgentValidator
from agent.models import ActionStatus, ActionRisk, PlannedAction
from data_engine.profiler import DataProfiler

def test_agent_planning():
    df = pd.DataFrame({
        "id": ["ORD-1", "ORD-1", "ORD-2"],
        "region": ["  North ", "  North ", "West"],
        "revenue": [100.0, 100.0, None],
        "units": [10, 10, 2000]
    })
    profile = DataProfiler.profile_dataset(df)
    plan = AgentPlanner.create_cleaning_plan(profile)

    assert len(plan) > 0
    # First action should be whitespace or duplicates
    action_ops = [a.operation_name for a in plan]
    assert "trim_whitespace" in action_ops
    assert "remove_duplicate_rows" in action_ops
    assert "impute_missing_numeric" in action_ops

def test_agent_safe_execution_and_validation():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    action = PlannedAction(
        action_id="ACT_01_TEST",
        issue_id="ISSUE_DUP",
        target_columns=["ALL"],
        operation_name="remove_duplicate_rows",
        parameters={},
        reason="Remove duplicates",
        risk_level=ActionRisk.SAFE,
        needs_approval=False
    )
    new_df, act_res, ev = AgentExecutor.execute_action(df, action)
    assert act_res.status == ActionStatus.PASSED
    assert len(new_df) == 2
    assert ev.status == "PASSED"

def test_agent_validation_rollback_on_failure():
    df = pd.DataFrame({"col": [1, 2, 3]})
    # An action that attempts to drop all rows or fails validation criteria
    action = PlannedAction(
        action_id="ACT_FAIL_TEST",
        issue_id="ISSUE_MISSING",
        target_columns=["col"],
        operation_name="impute_missing_numeric",
        parameters={"column": "non_existent_col"},
        reason="Test failure",
        risk_level=ActionRisk.REVIEW_RECOMMENDED,
        needs_approval=True
    )
    new_df, act_res, ev = AgentExecutor.execute_action(df, action)
    assert act_res.status in [ActionStatus.FAILED, ActionStatus.ROLLED_BACK]
    # State should remain completely unchanged
    assert len(new_df) == 3

"""Tests for SQLite persistence and session audit storage."""

import os
import pytest
from storage.db import DatabaseManager

@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_datapilot.db"
    manager = DatabaseManager(db_path=str(db_file))
    return manager

def test_session_lifecycle(test_db):
    session_id = "test_sess_001"
    # 1. Save session
    ok = test_db.save_or_update_session(
        session_id=session_id,
        dataset_name="sales.csv",
        row_count=100,
        col_count=5,
        initial_score=75.0,
        current_score=85.0,
        status="active"
    )
    assert ok is True

    # 2. Fetch session
    sess = test_db.get_session(session_id)
    assert sess is not None
    assert sess["dataset_name"] == "sales.csv"
    assert sess["row_count"] == 100

    # 3. Log activity
    test_db.log_activity(
        session_id=session_id,
        event_type="TEST_EVENT",
        decision_summary="Executed unit test event",
        status="PASSED"
    )
    logs = test_db.get_activity_logs(session_id)
    assert len(logs) == 1
    assert logs[0]["event_type"] == "TEST_EVENT"

    # 4. Log cleaning op
    test_db.log_cleaning_operation(
        session_id=session_id,
        operation_id="ACT_01",
        operation_name="trim_whitespace",
        target_columns="name",
        parameters={"cols": ["name"]},
        execution_status="PASSED",
        before_metrics={"rows": 100},
        after_metrics={"rows": 100}
    )
    manifest = test_db.get_cleaning_manifest(session_id)
    assert len(manifest) == 1
    assert manifest[0]["operation_name"] == "trim_whitespace"

    # 5. Delete session
    assert test_db.delete_session(session_id) is True
    assert test_db.get_session(session_id) is None

"""Session State and Snapshot Management for DataPilot AI."""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from agent.models import PlannedAction, AgentEvent
from agent.activity_log import ActivityLogger
from data_engine.profiler import DataProfiler
from data_engine.quality_score import QualityScoreCalculator
from storage.db import db_manager

logger = logging.getLogger(__name__)

class SessionState:
    """Encapsulates dataset versions, undo snapshots, active plan, and profiles."""

    def __init__(self, session_id: str = "default_session", dataset_name: str = "dataset"):
        self.session_id = session_id
        self.dataset_name = dataset_name
        
        self.original_df: Optional[pd.DataFrame] = None
        self.current_df: Optional[pd.DataFrame] = None
        
        self.undo_stack: List[Dict[str, Any]] = []
        self.plan: List[PlannedAction] = []
        self.logger = ActivityLogger(session_id=session_id)
        
        self.original_profile: Dict[str, Any] = {}
        self.current_profile: Dict[str, Any] = {}
        self.original_score: Dict[str, Any] = {}
        self.current_score: Dict[str, Any] = {}
        
        self.is_clean: bool = False

    def load_dataset(self, df: pd.DataFrame, dataset_name: str):
        """Initialize session with a newly loaded dataset."""
        self.dataset_name = dataset_name
        self.original_df = df.copy()
        self.current_df = df.copy()
        self.undo_stack.clear()
        self.plan.clear()
        self.logger.clear()

        # Initial Profiling and Scoring
        self.original_profile = DataProfiler.profile_dataset(self.original_df)
        self.current_profile = self.original_profile.copy()
        
        self.original_score = QualityScoreCalculator.calculate_score(self.original_profile)
        self.current_score = self.original_score.copy()

        self.logger.log(
            event_type="DATASET_LOADED",
            decision_summary=f"Loaded dataset '{dataset_name}' with {len(df)} rows and {len(df.columns)} columns.",
            details={"rows": len(df), "cols": len(df.columns)}
        )
        self.logger.log(
            event_type="PROFILING_COMPLETED",
            decision_summary=f"Profiling completed. Initial Quality Score: {self.original_score['overall_score']}/100 ({self.original_score['grade']}). Detected {len(self.original_profile.get('issues', []))} issue(s).",
            details={"score": self.original_score}
        )

        # Save session to DB
        schema_dict = {col: str(df[col].dtype) for col in df.columns}
        db_manager.save_or_update_session(
            session_id=self.session_id,
            dataset_name=dataset_name,
            row_count=len(df),
            col_count=len(df.columns),
            initial_score=self.original_score["overall_score"],
            current_score=self.current_score["overall_score"],
            status="active",
            schema_dict=schema_dict
        )

    def push_snapshot(self, description: str):
        """Save a snapshot of current dataset before a mutating operation."""
        if self.current_df is not None:
            self.undo_stack.append({
                "df": self.current_df.copy(),
                "description": description,
                "profile": self.current_profile.copy(),
                "score": self.current_score.copy()
            })
            # Limit undo stack to 20 snapshots to prevent memory bloat
            if len(self.undo_stack) > 20:
                self.undo_stack.pop(0)

    def undo_last_operation(self) -> bool:
        """Rollback to the most recent snapshot."""
        if not self.undo_stack:
            return False

        last_state = self.undo_stack.pop()
        self.current_df = last_state["df"]
        self.current_profile = last_state["profile"]
        self.current_score = last_state["score"]

        desc = last_state["description"]
        self.logger.log(
            event_type="UNDO_EXECUTED",
            decision_summary=f"Undid operation: '{desc}'. Restored prior dataset state.",
            status="RESTORED"
        )
        self._update_session_record()
        return True

    def reset_to_original(self):
        """Reset dataset to its original loaded condition."""
        if self.original_df is not None:
            self.current_df = self.original_df.copy()
            self.undo_stack.clear()
            self.plan.clear()
            self.current_profile = DataProfiler.profile_dataset(self.current_df)
            self.current_score = QualityScoreCalculator.calculate_score(self.current_profile)

            self.logger.log(
                event_type="RESET_TO_ORIGINAL",
                decision_summary="Dataset reset to pristine original upload.",
                status="RESTORED"
            )
            self._update_session_record()

    def update_after_mutation(self, new_df: pd.DataFrame, description: str):
        """Update working dataset and recompute profiles, metrics, and quality score."""
        self.current_df = new_df
        self.current_profile = DataProfiler.profile_dataset(self.current_df)
        self.current_score = QualityScoreCalculator.calculate_score(self.current_profile)
        self._update_session_record()

    def _update_session_record(self):
        """Sync updated metrics to SQLite database."""
        if self.current_df is not None:
            schema_dict = {col: str(self.current_df[col].dtype) for col in self.current_df.columns}
            db_manager.save_or_update_session(
                session_id=self.session_id,
                dataset_name=self.dataset_name,
                row_count=len(self.current_df),
                col_count=len(self.current_df.columns),
                initial_score=self.original_score.get("overall_score", 0.0),
                current_score=self.current_score.get("overall_score", 0.0),
                status="cleaned" if self.current_score.get("overall_score", 0) > self.original_score.get("overall_score", 0) else "active",
                schema_dict=schema_dict
            )

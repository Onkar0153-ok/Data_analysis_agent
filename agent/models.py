"""Agent data structures and state definitions for DataPilot AI."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

class ActionRisk:
    SAFE = "SAFE"
    REVIEW_RECOMMENDED = "REVIEW RECOMMENDED"
    HIGH_RISK = "HIGH RISK"

class ActionStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    SKIPPED = "SKIPPED"

@dataclass
class PlannedAction:
    action_id: str
    issue_id: str
    target_columns: List[str]
    operation_name: str
    parameters: Dict[str, Any]
    reason: str
    risk_level: str
    needs_approval: bool
    status: str = ActionStatus.PENDING
    retry_count: int = 0
    max_retries: int = 2
    execution_result: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None

@dataclass
class AgentEvent:
    timestamp: str
    event_type: str
    action_id: Optional[str]
    decision_summary: str
    status: str
    validation_result: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, event_type: str, decision_summary: str, action_id: Optional[str] = None,
               status: str = "COMPLETED", validation_result: Optional[str] = None, details: Optional[Dict] = None):
        return cls(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            event_type=event_type,
            action_id=action_id,
            decision_summary=decision_summary,
            status=status,
            validation_result=validation_result,
            details=details or {}
        )

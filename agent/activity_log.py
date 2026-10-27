"""Activity and Event Logging for DataPilot AI Agent."""

from typing import List, Dict, Any, Optional
from agent.models import AgentEvent
from storage.db import db_manager

class ActivityLogger:
    """Manages ordered event logging for agent transparency and UI trace."""

    def __init__(self, session_id: str = "default_session"):
        self.session_id = session_id
        self.events: List[AgentEvent] = []

    def log(self, event_type: str, decision_summary: str, action_id: Optional[str] = None,
            status: str = "COMPLETED", validation_result: Optional[str] = None,
            details: Optional[Dict] = None) -> AgentEvent:
        """Create, store in-memory, and persist event to database."""
        event = AgentEvent.create(
            event_type=event_type,
            decision_summary=decision_summary,
            action_id=action_id,
            status=status,
            validation_result=validation_result,
            details=details or {}
        )
        self.events.append(event)
        
        # Persist to SQLite
        db_manager.log_activity(
            session_id=self.session_id,
            event_type=event_type,
            decision_summary=decision_summary,
            action_id=action_id,
            status=status,
            validation_result=validation_result,
            details=details
        )
        return event

    def get_events(self) -> List[AgentEvent]:
        """Return all logged events in chronological order."""
        return self.events

    def clear(self):
        """Clear session events."""
        self.events.clear()

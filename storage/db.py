"""SQLite Database Management for DataPilot AI."""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from config.settings import SQLITE_DB_PATH

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite storage for sessions, operations, activity logs, and chat."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or SQLITE_DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-safe connection with row factory."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables if they do not exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 1. analysis_sessions
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_sessions (
                        session_id TEXT PRIMARY KEY,
                        dataset_name TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        row_count INTEGER,
                        col_count INTEGER,
                        initial_quality_score REAL,
                        current_quality_score REAL,
                        status TEXT,
                        schema_json TEXT
                    )
                """)
                # 2. agent_activity
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS agent_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        action_id TEXT,
                        decision_summary TEXT NOT NULL,
                        status TEXT NOT NULL,
                        validation_result TEXT,
                        details_json TEXT,
                        FOREIGN KEY (session_id) REFERENCES analysis_sessions (session_id) ON DELETE CASCADE
                    )
                """)
                # 3. cleaning_operations
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cleaning_operations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        operation_id TEXT NOT NULL,
                        operation_name TEXT NOT NULL,
                        target_columns TEXT,
                        parameters_json TEXT,
                        execution_status TEXT NOT NULL,
                        before_metrics_json TEXT,
                        after_metrics_json TEXT,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES analysis_sessions (session_id) ON DELETE CASCADE
                    )
                """)
                # 4. chat_history
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_question TEXT NOT NULL,
                        tool_used TEXT,
                        result_summary TEXT,
                        chart_type TEXT,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES analysis_sessions (session_id) ON DELETE CASCADE
                    )
                """)
                # 5. saved_reports
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS saved_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        report_filename TEXT NOT NULL,
                        report_type TEXT NOT NULL,
                        content TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES analysis_sessions (session_id) ON DELETE CASCADE
                    )
                """)
                conn.commit()
                logger.info("Database initialized successfully at %s", self.db_path)
        except Exception as e:
            logger.error("Failed to initialize database: %s", e)

    # --- Session Operations ---
    def save_or_update_session(self, session_id: str, dataset_name: str, row_count: int,
                               col_count: int, initial_score: float = 0.0,
                               current_score: float = 0.0, status: str = "active",
                               schema_dict: Optional[Dict] = None) -> bool:
        """Create or update an analysis session record."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT session_id FROM analysis_sessions WHERE session_id = ?", (session_id,))
                exists = cursor.fetchone()
                schema_json = json.dumps(schema_dict or {})
                now_str = datetime.now().isoformat()

                if exists:
                    cursor.execute("""
                        UPDATE analysis_sessions
                        SET row_count = ?, col_count = ?, current_quality_score = ?, status = ?, schema_json = ?
                        WHERE session_id = ?
                    """, (row_count, col_count, current_score, status, schema_json, session_id))
                else:
                    cursor.execute("""
                        INSERT INTO analysis_sessions
                        (session_id, dataset_name, created_at, row_count, col_count,
                         initial_quality_score, current_quality_score, status, schema_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (session_id, dataset_name, now_str, row_count, col_count,
                          initial_score, current_score, status, schema_json))
                conn.commit()
                return True
        except Exception as e:
            logger.error("Error saving session %s: %s", session_id, e)
            return False

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """List all analysis sessions ordered by recent."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM analysis_sessions ORDER BY created_at DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error fetching sessions: %s", e)
            return []

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single session metadata."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM analysis_sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error("Error fetching session %s: %s", session_id, e)
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and associated records."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM agent_activity WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM cleaning_operations WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM saved_reports WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM analysis_sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error("Error deleting session %s: %s", session_id, e)
            return False

    def clear_all_history(self) -> bool:
        """Clear all historical sessions and records."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM agent_activity")
                cursor.execute("DELETE FROM cleaning_operations")
                cursor.execute("DELETE FROM chat_history")
                cursor.execute("DELETE FROM saved_reports")
                cursor.execute("DELETE FROM analysis_sessions")
                conn.commit()
                return True
        except Exception as e:
            logger.error("Error clearing all history: %s", e)
            return False

    # --- Agent Activity Logs ---
    def log_activity(self, session_id: str, event_type: str, decision_summary: str,
                     action_id: Optional[str] = None, status: str = "COMPLETED",
                     validation_result: Optional[str] = None,
                     details: Optional[Dict] = None) -> bool:
        """Record an agent activity event."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now_str = datetime.now().isoformat()
                cursor.execute("""
                    INSERT INTO agent_activity
                    (session_id, timestamp, event_type, action_id, decision_summary, status, validation_result, details_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (session_id, now_str, event_type, action_id, decision_summary, status,
                      validation_result, json.dumps(details or {})))
                conn.commit()
                return True
        except Exception as e:
            logger.error("Error logging activity: %s", e)
            return False

    def get_activity_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Get activity logs for a session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM agent_activity WHERE session_id = ? ORDER BY id ASC", (session_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error fetching activity logs: %s", e)
            return []

    # --- Cleaning Operations & Manifest ---
    def log_cleaning_operation(self, session_id: str, operation_id: str,
                               operation_name: str, target_columns: str,
                               parameters: Dict, execution_status: str,
                               before_metrics: Dict, after_metrics: Dict) -> bool:
        """Record a cleaning operation."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now_str = datetime.now().isoformat()
                cursor.execute("""
                    INSERT INTO cleaning_operations
                    (session_id, operation_id, operation_name, target_columns,
                     parameters_json, execution_status, before_metrics_json, after_metrics_json, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (session_id, operation_id, operation_name, target_columns,
                      json.dumps(parameters), execution_status,
                      json.dumps(before_metrics), json.dumps(after_metrics), now_str))
                conn.commit()
                return True
        except Exception as e:
            logger.error("Error logging cleaning operation: %s", e)
            return False

    def get_cleaning_manifest(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the ordered cleaning operations for a session to enable replay."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM cleaning_operations WHERE session_id = ? ORDER BY id ASC", (session_id,))
                rows = cursor.fetchall()
                manifest = []
                for r in rows:
                    item = dict(r)
                    item["parameters"] = json.loads(item["parameters_json"]) if item.get("parameters_json") else {}
                    item["before_metrics"] = json.loads(item["before_metrics_json"]) if item.get("before_metrics_json") else {}
                    item["after_metrics"] = json.loads(item["after_metrics_json"]) if item.get("after_metrics_json") else {}
                    manifest.append(item)
                return manifest
        except Exception as e:
            logger.error("Error fetching cleaning manifest: %s", e)
            return []

    # --- Chat History ---
    def log_chat_interaction(self, session_id: str, user_question: str,
                             tool_used: Optional[str] = None,
                             result_summary: Optional[str] = None,
                             chart_type: Optional[str] = None) -> bool:
        """Save a chat interaction to history."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now_str = datetime.now().isoformat()
                cursor.execute("""
                    INSERT INTO chat_history
                    (session_id, user_question, tool_used, result_summary, chart_type, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (session_id, user_question, tool_used, result_summary, chart_type, now_str))
                conn.commit()
                return True
        except Exception as e:
            logger.error("Error logging chat: %s", e)
            return False

    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Fetch chat history for a session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chat_history WHERE session_id = ? ORDER BY id ASC", (session_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error fetching chat history: %s", e)
            return []

    # --- Saved Reports ---
    def save_report(self, session_id: str, filename: str, report_type: str, content: str) -> bool:
        """Save an analysis report."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now_str = datetime.now().isoformat()
                cursor.execute("""
                    INSERT INTO saved_reports
                    (session_id, report_filename, report_type, content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, filename, report_type, content, now_str))
                conn.commit()
                return True
        except Exception as e:
            logger.error("Error saving report: %s", e)
            return False

    def get_saved_reports(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve reports."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if session_id:
                    cursor.execute("SELECT * FROM saved_reports WHERE session_id = ? ORDER BY id DESC", (session_id,))
                else:
                    cursor.execute("SELECT * FROM saved_reports ORDER BY id DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Error fetching reports: %s", e)
            return []

# Singleton instance
db_manager = DatabaseManager()

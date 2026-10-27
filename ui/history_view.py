"""SQLite Session History and Audit Viewer UI for DataPilot AI."""

import json
import streamlit as st
import pandas as pd
from storage.db import db_manager

def render_history_view():
    """Render the SQLite session history, operation manifests, and audit logs."""
    st.markdown("## 📜 Analysis History & Audit Vault (SQLite)")
    st.markdown("Inspect persistent historical analysis sessions, audit trails, and recorded transformation logs.")

    sessions = db_manager.get_all_sessions()

    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.write(f"Total Persisted Sessions: **{len(sessions)}**")
    with col_h2:
        if st.button("🗑️ Clear Entire History", type="secondary", use_container_width=True):
            if db_manager.clear_all_history():
                st.success("All session history cleared.")
                st.rerun()

    if not sessions:
        st.info("No saved sessions in SQLite database yet. Upload a dataset to create an active session.")
        return

    # Session Selection Table
    df_sessions = pd.DataFrame(sessions)[["session_id", "dataset_name", "created_at", "row_count", "col_count", "initial_quality_score", "current_quality_score", "status"]]
    st.dataframe(df_sessions, use_container_width=True, hide_index=True)

    # Detailed Session Inspection
    selected_sess_id = st.selectbox(
        "Select Session ID to Inspect Audit Logs:",
        options=[s["session_id"] for s in sessions],
        format_func=lambda x: f"{x} - {next((s['dataset_name'] for s in sessions if s['session_id'] == x), '')}"
    )

    if selected_sess_id:
        sess_data = next((s for s in sessions if s["session_id"] == selected_sess_id), None)
        
        tab_ops, tab_audit, tab_chat = st.tabs([
            "🛠️ Cleaning Manifest", "📡 Agent Activity Log", "💬 Chat History"
        ])

        with tab_ops:
            manifest = db_manager.get_cleaning_manifest(selected_sess_id)
            if manifest:
                st.markdown(f"**Recorded Operations ({len(manifest)}):**")
                st.dataframe(pd.DataFrame(manifest)[["operation_id", "operation_name", "target_columns", "execution_status", "timestamp"]], use_container_width=True, hide_index=True)
            else:
                st.info("No cleaning operations logged for this session.")

        with tab_audit:
            logs = db_manager.get_activity_logs(selected_sess_id)
            if logs:
                st.markdown(f"**Activity Events ({len(logs)}):**")
                for log in logs:
                    st.markdown(
                        f"<div class='event-entry'>"
                        f"<span class='event-time'>{log['timestamp']}</span> "
                        f"<strong>[{log['event_type']}]</strong>: {log['decision_summary']} "
                        f"&bull; Status: <code>{log['status']}</code>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.info("No activity logs recorded for this session.")

        with tab_chat:
            chat_logs = db_manager.get_chat_history(selected_sess_id)
            if chat_logs:
                for c in chat_logs:
                    st.markdown(f"**User ({c['timestamp']}):** {c['user_question']}")
                    st.markdown(f"**Agent:** {c['result_summary']}")
                    if c.get("tool_used"):
                        st.caption(f"Tool executed: `{c['tool_used']}`")
                    st.markdown("---")
            else:
                st.info("No chat interactions recorded for this session.")

        # Delete single session
        if st.button(f"❌ Delete Session '{selected_sess_id}'", type="secondary"):
            if db_manager.delete_session(selected_sess_id):
                st.success(f"Session {selected_sess_id} deleted successfully.")
                st.rerun()

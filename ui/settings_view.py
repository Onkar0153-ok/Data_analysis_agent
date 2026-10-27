"""Settings and Agent Diagnostics UI for DataPilot AI."""

import os
import streamlit as st
from config.settings import SQLITE_DB_PATH, GEMINI_MODEL
from llm.client import LLMClient
from agent.state import SessionState

def render_settings(state: SessionState):
    """Render Settings, LLM authentication test, and diagnostic log console."""
    st.markdown("## ⚙️ Settings & Agent Diagnostics")
    st.markdown("Configure LLM credentials, adjust autonomous policy thresholds, and inspect raw runtime diagnostics.")

    tab_llm, tab_policy, tab_logs = st.tabs([
        "🔑 LLM Configuration", "🛡️ Agent Risk Policies", "📋 Runtime Diagnostics"
    ])

    with tab_llm:
        st.markdown("### LLM Provider Settings")
        st.caption("DataPilot AI uses Google Gemini function calling for natural-language queries. An API key is optional.")

        current_key = os.getenv("GEMINI_API_KEY", "")
        api_key_input = st.text_input(
            "Google Gemini API Key:",
            value=current_key,
            type="password",
            help="Enter your Gemini API key. Keys are held in environment memory and never persisted in database files."
        )

        col_save, col_test = st.columns(2)
        with col_save:
            if st.button("💾 Save Key to Session", use_container_width=True):
                os.environ["GEMINI_API_KEY"] = api_key_input
                st.success("API Key updated in session memory!")
                st.rerun()

        with col_test:
            if st.button("🔌 Test API Connection", use_container_width=True):
                if not api_key_input:
                    st.warning("Please enter an API key first.")
                else:
                    with st.spinner("Testing connection with Google Gemini..."):
                        try:
                            from google import genai
                            client = genai.Client(api_key=api_key_input)
                            resp = client.models.generate_content(
                                model=GEMINI_MODEL,
                                contents="Hello DataPilot! Reply with 'Connection successful!'."
                            )
                            st.success(f"✅ Gemini API Test Passed! Response: {resp.text.strip()}")
                        except Exception as e:
                            st.error(f"❌ Gemini API Test Failed: {str(e)}")

        st.markdown("---")
        client = LLMClient()
        avail, status = client.is_available()
        st.write(f"**Current Status:** {'🟢' if avail else '🟡'} {status}")

    with tab_policy:
        st.markdown("### Autonomous Execution Policies")
        st.caption("Configure which actions the agent may execute autonomously versus requiring explicit confirmation.")

        st.checkbox("Auto-execute SAFE operations (whitespace trimming, case normalization, deduplication)", value=True, disabled=True)
        st.caption("Policy: SAFE operations do not destroy valid observations or alter statistical meaning.")

        st.checkbox("Require approval for REVIEW RECOMMENDED operations (imputation, type conversions)", value=True)
        st.caption("Policy: Numerical and categorical imputations introduce modeled values.")

        st.checkbox("Require approval for HIGH RISK operations (outlier row deletion, dropping columns)", value=True, disabled=True)
        st.caption("Locked for safety: Destructive data loss always requires explicit user consent.")

    with tab_logs:
        st.markdown("### Runtime Event Stream")
        events = state.logger.get_events()
        if events:
            for ev in reversed(events):
                st.code(
                    f"[{ev.timestamp}] [{ev.event_type}] [STATUS: {ev.status}]\n"
                    f"Summary: {ev.decision_summary}\n"
                    f"Validation: {ev.validation_result or 'N/A'}\n"
                    f"Details: {ev.details}",
                    language="text"
                )
        else:
            st.info("No runtime events logged yet.")

        st.markdown("---")
        st.write(f"**SQLite Database Path:** `{SQLITE_DB_PATH}`")

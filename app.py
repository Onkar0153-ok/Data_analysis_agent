"""DataPilot AI - Autonomous AI Agent for Intelligent Data Analysis, Visualization, and Data Preparation.

Main application entrypoint.
"""

import uuid
import streamlit as st
import pandas as pd

from config.settings import THEME
from utils.logging_config import setup_logging
from agent.state import SessionState
from data_engine.loader import DatasetLoader
from llm.client import LLMClient
from ui.styles import get_custom_css
from ui.overview import render_overview
from ui.explorer import render_explorer
from ui.autopilot import render_autopilot
from ui.visualizations import render_visualizations
from ui.ask_data import render_ask_data
from ui.cleaning import render_cleaning
from ui.reports import render_reports
from ui.history_view import render_history_view
from ui.settings_view import render_settings

# Setup logging
setup_logging()

# Streamlit Page Configuration
st.set_page_config(
    page_title="DataPilot AI — Autonomous Data Analysis Agent",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Theme & Custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Initialize Session State
if "session_id" not in st.session_state:
    st.session_state.session_id = f"sess_{uuid.uuid4().hex[:8]}"

if "agent_state" not in st.session_state:
    st.session_state.agent_state = SessionState(session_id=st.session_state.session_id)

state: SessionState = st.session_state.agent_state

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h2 style='color: #22D3EE; margin-bottom: 0;'>✈️ DataPilot AI</h2>", unsafe_allow_html=True)
    st.caption("Autonomous Agent for Data Analysis & Prep")
    st.markdown("---")

    # Navigation
    nav_choice = st.radio(
        "Navigation",
        [
            "📊 Overview",
            "🔎 Data Explorer",
            "🤖 AutoPilot Agent",
            "📈 Visualizations",
            "💬 Ask Your Data",
            "🧹 Data Cleaning",
            "📑 Reports & Exports",
            "📜 History & Sessions",
            "⚙️ Settings & Agent Logs",
        ],
        index=0
    )

    st.markdown("---")

    # Dataset Status in Sidebar
    if state.current_df is not None:
        score_val = state.current_score.get("overall_score", 0.0)
        grade_val = state.current_score.get("grade", "N/A")
        score_color = "#10B981" if score_val >= 80 else "#F59E0B"

        st.markdown(
            f"<div style='background: #141F32; border: 1px solid #273449; border-radius: 8px; padding: 12px; margin-bottom: 12px;'>"
            f"<span style='font-size: 11px; color: #94A3B8; text-transform: uppercase;'>Loaded Dataset</span><br>"
            f"<strong style='color: #22D3EE; font-size: 14px;'>{state.dataset_name}</strong><br>"
            f"<span style='color: #F8FAFC; font-size: 12px;'>{len(state.current_df)} rows &bull; {len(state.current_df.columns)} cols</span><br>"
            f"<div style='margin-top: 8px; display: flex; justify-content: space-between; align-items: center;'>"
            f"<span style='font-size: 12px; color: #94A3B8;'>Quality:</span>"
            f"<span style='color: {score_color}; font-weight: bold; font-size: 14px;'>{score_val}/100 ({grade_val})</span>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )

        # Quick Actions
        col_sb1, col_sb2 = st.columns(2)
        with col_sb1:
            if st.button("↩️ Undo", disabled=(len(state.undo_stack) == 0), use_container_width=True):
                if state.undo_last_operation():
                    st.toast("Reverted last change!")
                    st.rerun()
        with col_sb2:
            if st.button("🔄 Reset", use_container_width=True):
                state.reset_to_original()
                st.toast("Restored original dataset!")
                st.rerun()

    else:
        st.info("No active dataset loaded.")
        if st.button("🚀 Load Sample Sales", use_container_width=True):
            df_sample, meta = DatasetLoader.load_sample_dataset()
            if df_sample is not None:
                state.load_dataset(df_sample, "sample_sales.csv")
                st.toast("Sample Sales dataset loaded!")
                st.rerun()

    st.markdown("---")

    # LLM Status Indicator
    llm_client = LLMClient()
    is_llm_ready, llm_msg = llm_client.is_available()
    llm_badge = "🟢 Online" if is_llm_ready else "🟡 Fallback"
    st.markdown(
        f"<div style='font-size: 12px; color: #94A3B8;'>"
        f"LLM Engine: <strong style='color: #F8FAFC;'>{llm_badge}</strong><br>"
        f"<span style='font-size: 10px; color: #64748B;'>{'Gemini Function Calling' if is_llm_ready else 'Deterministic Parser'}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

# --- Main Content Router ---
if nav_choice == "📊 Overview":
    render_overview(state)
elif nav_choice == "🔎 Data Explorer":
    render_explorer(state)
elif nav_choice == "🤖 AutoPilot Agent":
    render_autopilot(state)
elif nav_choice == "📈 Visualizations":
    render_visualizations(state)
elif nav_choice == "💬 Ask Your Data":
    render_ask_data(state)
elif nav_choice == "🧹 Data Cleaning":
    render_cleaning(state)
elif nav_choice == "📑 Reports & Exports":
    render_reports(state)
elif nav_choice == "📜 History & Sessions":
    render_history_view()
elif nav_choice == "⚙️ Settings & Agent Logs":
    render_settings(state)

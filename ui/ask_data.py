"""Ask Your Data Conversational UI for DataPilot AI."""

import streamlit as st
import pandas as pd
from agent.state import SessionState
from llm.client import LLMClient
from storage.db import db_manager

def render_ask_data(state: SessionState):
    """Render the Ask Your Data chat interface."""
    st.markdown("## 💬 Ask Your Data — LLM Agent")
    st.markdown("Ask natural-language questions about your actual dataset. Calculations are executed strictly in Python/Pandas via controlled tool calls.")

    if state.current_df is None:
        st.info("No active dataset. Please upload or load a sample dataset in the Overview tab.")
        return

    # Initialize LLM Client
    client = LLMClient()
    available, status_msg = client.is_available()

    # Provider status banner
    if available:
        st.success(f"🟢 **LLM Status:** {status_msg}")
    else:
        st.warning(f"🟡 **LLM Status:** {status_msg} (Deterministic fallback active. You can add an API key in Settings).")

    # Sample Quick Questions
    st.markdown("#### 💡 Quick Questions:")
    sample_q_cols = st.columns(3)
    quick_q = None

    with sample_q_cols[0]:
        if st.button("📊 Dataset Summary", use_container_width=True):
            quick_q = "Give me a summary of this dataset"
        if st.button("❓ Missing Values Report", use_container_width=True):
            quick_q = "Which columns have the most missing values?"

    with sample_q_cols[1]:
        if st.button("🏆 Highest Revenue Region", use_container_width=True):
            quick_q = "Which region has the highest average revenue?"
        if st.button("📦 Top 5 Units Orders", use_container_width=True):
            quick_q = "What are the top 5 records by units?"

    with sample_q_cols[2]:
        if st.button("🔗 Price vs Revenue Correlation", use_container_width=True):
            quick_q = "What is the correlation between price and revenue?"
        if st.button("🎯 Outliers in Units", use_container_width=True):
            quick_q = "Detect outliers in Units"

    # Chat session storage in Streamlit state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Display past messages
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tool"):
                st.caption(f"🔧 *Executed tool: `{msg['tool']}`*")
            if msg.get("chart") is not None:
                st.plotly_chart(msg["chart"], use_container_width=True)

    # Question Input
    user_input = st.chat_input("Ask a question about the dataset (e.g. 'Average revenue by region' or 'Top 5 records by price')...")
    
    question_to_process = quick_q or user_input

    if question_to_process:
        # Append user message
        st.session_state.chat_messages.append({"role": "user", "content": question_to_process})
        with st.chat_message("user"):
            st.markdown(question_to_process)

        # Process with LLM Client
        with st.chat_message("assistant"):
            with st.spinner("Analyzing dataset and executing Pandas computation..."):
                response = client.ask(
                    question=question_to_process,
                    df=state.current_df,
                    profile=state.current_profile,
                    quality_score=state.current_score,
                    session_id=state.session_id
                )

                answer_text = response.get("answer", "")
                tool_used = response.get("tool_used")
                chart_obj = response.get("chart")

                st.markdown(answer_text)
                if tool_used:
                    st.caption(f"🔧 *Executed tool: `{tool_used}` ({response.get('mode')})*")
                if chart_obj:
                    st.plotly_chart(chart_obj, use_container_width=True)

                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": answer_text,
                    "tool": tool_used,
                    "chart": chart_obj
                })

    # Clear chat button
    if st.session_state.chat_messages:
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Chat Display", use_container_width=False):
            st.session_state.chat_messages = []
            st.rerun()

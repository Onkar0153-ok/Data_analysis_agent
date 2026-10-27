"""Overview and Ingestion UI for DataPilot AI."""

import streamlit as st
import pandas as pd
from agent.state import SessionState
from data_engine.loader import DatasetLoader

def render_overview(state: SessionState):
    """Render the main Overview page."""
    st.markdown("## 📊 Dataset Overview & Health Profile")
    st.markdown("Upload your tabular data (CSV, TSV, XLSX) or load the realistic demonstration dataset to initialize the agent.")

    # Ingestion Controls
    col_upload, col_sample = st.columns([3, 2])
    
    with col_upload:
        uploaded_file = st.file_uploader(
            "Upload Dataset (CSV, TSV, Excel)",
            type=["csv", "tsv", "xlsx"],
            help="Supports standard formats up to 50MB with automatic delimiter & encoding detection."
        )
        if uploaded_file is not None:
            # Check if this is a newly uploaded file
            if state.dataset_name != uploaded_file.name:
                with st.spinner("Ingesting and profiling dataset..."):
                    df, meta = DatasetLoader.load_from_file(uploaded_file, uploaded_file.name)
                    if df is not None and meta["success"]:
                        state.load_dataset(df, uploaded_file.name)
                        st.success(f"Successfully loaded '{uploaded_file.name}' ({len(df)} rows, {len(df.columns)} columns)!")
                        st.rerun()
                    else:
                        st.error(f"Failed to load file: {meta.get('error')}")

    with col_sample:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 Load Sample Sales Dataset (Demo)", use_container_width=True, type="primary"):
            with st.spinner("Loading demo dataset with controlled issues..."):
                df_sample, meta = DatasetLoader.load_sample_dataset()
                if df_sample is not None:
                    state.load_dataset(df_sample, "sample_sales.csv")
                    st.success("Sample Sales dataset loaded successfully!")
                    st.rerun()
                else:
                    st.error(f"Error loading sample: {meta.get('error')}")

        st.caption("Includes controlled duplicate rows, whitespace flaws, missing values, and inconsistent category casing for agent demonstration.")

    # If dataset is loaded, show status and metric cards
    if state.current_df is None:
        st.info("👆 Please upload a file or click 'Load Sample Sales Dataset' to begin data analysis.")
        return

    st.markdown("---")

    # Dataset Status Banner
    st.markdown(
        f"<div class='datapilot-card' style='display: flex; justify-content: space-between; align-items: center;'>"
        f"<div>"
        f"<span style='color: #94A3B8; font-size: 13px;'>ACTIVE DATASET</span><br>"
        f"<strong style='font-size: 18px; color: #22D3EE;'>{state.dataset_name}</strong> "
        f"<span style='color: #94A3B8; font-size: 13px;'>({len(state.current_df)} rows &bull; {len(state.current_df.columns)} columns)</span>"
        f"</div>"
        f"<div>"
        f"<span class='badge-safe' style='font-size: 13px;'>Session ID: {state.session_id}</span>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Metric Cards Grid
    profile = state.current_profile
    score = state.current_score
    issues_count = len(profile.get("issues", []))

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"<div class='datapilot-card'>"
            f"<div class='metric-title'>Quality Score</div>"
            f"<div class='metric-value' style='color: {'#10B981' if score.get('overall_score', 0) >= 80 else '#F59E0B'};'>"
            f"{score.get('overall_score', 0)}<span style='font-size: 16px; color: #94A3B8;'>/100</span>"
            f"</div>"
            f"<div class='metric-sub'>Grade {score.get('grade', 'N/A')} &bull; Heuristic</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    with c2:
        missing_rate = profile.get("missing_rate", 0.0)
        st.markdown(
            f"<div class='datapilot-card'>"
            f"<div class='metric-title'>Missing Cells</div>"
            f"<div class='metric-value'>{profile.get('missing_cells', 0)}</div>"
            f"<div class='metric-sub'>{missing_rate:.1%} of total cells</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    with c3:
        dup_rows = profile.get("duplicate_rows", 0)
        st.markdown(
            f"<div class='datapilot-card'>"
            f"<div class='metric-title'>Duplicate Rows</div>"
            f"<div class='metric-value'>{dup_rows}</div>"
            f"<div class='metric-sub'>{profile.get('duplicate_rate', 0.0):.1%} redundancy rate</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"<div class='datapilot-card'>"
            f"<div class='metric-title'>Perceived Issues</div>"
            f"<div class='metric-value' style='color: {'#EF4444' if issues_count > 0 else '#10B981'};'>{issues_count}</div>"
            f"<div class='metric-sub'>Requiring action/review</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    # Quality Breakdown Accordion
    with st.expander("🔍 Explainable Data Quality Score Breakdown", expanded=False):
        st.markdown(f"**Explanation:** {score.get('explanation', '')}")
        breakdown = score.get("breakdown", {})
        
        b1, b2, b3, b4 = st.columns(4)
        for col_widget, (dim_name, dim_data) in zip([b1, b2, b3, b4], breakdown.items()):
            with col_widget:
                pct = dim_data.get("percentage", 0.0)
                st.write(f"**{dim_name.title()}** ({dim_data.get('score')}/{dim_data.get('max')} pts)")
                st.progress(pct / 100.0)
                st.caption(dim_data.get("notes", ""))

    # Dataset Preview & Schema
    st.markdown("### 📋 Dataset Preview")
    view_option = st.radio(
        "Display Version:",
        ["Current Working Dataset", "Original Uploaded Dataset"],
        horizontal=True
    )
    preview_df = state.current_df if view_option == "Current Working Dataset" else state.original_df
    if preview_df is not None:
        st.dataframe(preview_df.head(10), use_container_width=True)

    # Quick Issues Highlight
    if issues_count > 0:
        st.markdown("### ⚠️ Critical Detected Issues")
        for issue in profile.get("issues", [])[:4]:
            sev_badge = (
                "<span class='badge-high-risk'>HIGH</span>" if issue["severity"] == "HIGH"
                else "<span class='badge-review'>MEDIUM</span>" if issue["severity"] == "MEDIUM"
                else "<span class='badge-safe'>LOW</span>"
            )
            st.markdown(
                f"<div class='event-entry'>"
                f"{sev_badge} <strong>{issue['type'].replace('_', ' ').title()}</strong>: {issue['description']}"
                f"</div>",
                unsafe_allow_html=True
            )
        if issues_count > 4:
            st.caption(f"+ {issues_count - 4} additional issue(s) detected. View the AutoPilot Agent tab to review the complete cleaning plan.")

"""Reports, Exports, and Manifest Replay UI for DataPilot AI."""

import json
import streamlit as st
import pandas as pd
from agent.state import SessionState
from data_engine.comparison import ComparisonEngine
from utils.export import ReportExporter
from storage.db import db_manager

def render_reports(state: SessionState):
    """Render Before-and-After Comparison, Exports, and Manifest Replay."""
    st.markdown("## 📑 Reports, Exports & Operation Manifests")
    st.markdown("Generate executive reports, download cleaned data, and export reproducible operation manifests.")

    if state.current_df is None:
        st.info("No active dataset. Please upload or load a sample dataset in the Overview tab.")
        return

    # Compute Before-and-After Comparison
    comparison = ComparisonEngine.compare_states(
        original_df=state.original_df,
        current_df=state.current_df,
        original_profile=state.original_profile,
        current_profile=state.current_profile,
        original_score=state.original_score,
        current_score=state.current_score,
        activity_logs=[ev.__dict__ for ev in state.logger.get_events()]
    )

    tab_comp, tab_exports, tab_replay = st.tabs([
        "⚖️ Before-and-After Comparison", "💾 Export Artifacts", "🔁 Manifest Replay Studio"
    ])

    with tab_comp:
        st.markdown("### 📊 Comprehensive Transformation Audit")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            score_diff = comparison["score_delta"]
            diff_color = "#10B981" if score_diff >= 0 else "#EF4444"
            st.markdown(
                f"<div class='datapilot-card'>"
                f"<div class='metric-title'>Quality Score Delta</div>"
                f"<div class='metric-value' style='color: {diff_color};'>{comparison['score_before']} &rarr; {comparison['score_after']}</div>"
                f"<div class='metric-sub'>Delta: {score_diff:+} pts ({comparison['grade_before']} &rarr; {comparison['grade_after']})</div>"
                f"</div>",
                unsafe_allow_html=True
            )

        with c2:
            st.markdown(
                f"<div class='datapilot-card'>"
                f"<div class='metric-title'>Dimensions</div>"
                f"<div class='metric-value'>{comparison['rows_before']} &rarr; {comparison['rows_after']}</div>"
                f"<div class='metric-sub'>{comparison['rows_diff']:+} rows &bull; {comparison['cols_diff']:+} cols</div>"
                f"</div>",
                unsafe_allow_html=True
            )

        with c3:
            st.markdown(
                f"<div class='datapilot-card'>"
                f"<div class='metric-title'>Missing Values</div>"
                f"<div class='metric-value'>{comparison['missing_before']} &rarr; {comparison['missing_after']}</div>"
                f"<div class='metric-sub'>{comparison['missing_rate_before']:.1%} &rarr; {comparison['missing_rate_after']:.1%}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

        with c4:
            st.markdown(
                f"<div class='datapilot-card'>"
                f"<div class='metric-title'>Operations Executed</div>"
                f"<div class='metric-value'>{comparison['completed_ops']}</div>"
                f"<div class='metric-sub'>{comparison['rolled_back_ops']} rollbacks &bull; {comparison['skipped_ops']} skipped</div>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.markdown("#### Column-by-Column Status")
        st.dataframe(comparison["column_comparison_df"], use_container_width=True, hide_index=True)

    with tab_exports:
        st.markdown("### 📥 Download Cleaned Artifacts")
        
        col_csv, col_html, col_manifest = st.columns(3)

        # 1. Cleaned CSV Download
        with col_csv:
            csv_bytes = state.current_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📄 Download Cleaned CSV",
                data=csv_bytes,
                file_name=f"cleaned_{state.dataset_name}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.caption("Standard RFC 4180 CSV with normalized values and preserved headers.")

        # 2. HTML Report Download
        with col_html:
            manifest_data = db_manager.get_cleaning_manifest(state.session_id)
            html_report = ReportExporter.generate_html_report(
                metadata={"filename": state.dataset_name},
                profile_before=state.original_profile,
                profile_after=state.current_profile,
                score_before=state.original_score,
                score_after=state.current_score,
                operations_manifest=manifest_data,
                activity_logs=[ev.__dict__ for ev in state.logger.get_events()],
                comparison_metrics=comparison
            )
            st.download_button(
                label="📑 Download HTML Report",
                data=html_report.encode("utf-8"),
                file_name=f"DataPilot_Report_{state.dataset_name}.html",
                mime="text/html",
                use_container_width=True
            )
            st.caption("Standalone executive report with scores, before/after metrics, and audit log.")

        # 3. JSON Operation Manifest
        with col_manifest:
            manifest_json = json.dumps(manifest_data, indent=2)
            st.download_button(
                label="⚙️ Export Operation Manifest",
                data=manifest_json.encode("utf-8"),
                file_name=f"manifest_{state.dataset_name}.json",
                mime="application/json",
                use_container_width=True
            )
            st.caption("Reproducible pipeline recipe for replaying transformations on new datasets.")

    with tab_replay:
        st.markdown("### 🔁 Replay Operation Manifest")
        st.markdown("Validate and re-execute a recorded sequence of cleaning operations against the current dataset.")

        uploaded_manifest_file = st.file_uploader("Upload Operation Manifest (.json):", type=["json"], key="replay_manifest_uploader")
        
        manifest_to_replay = None
        if uploaded_manifest_file is not None:
            try:
                manifest_to_replay = json.load(uploaded_manifest_file)
                st.success(f"Loaded manifest with {len(manifest_to_replay)} operation(s).")
            except Exception as e:
                st.error(f"Failed to parse manifest JSON: {e}")
        else:
            # Offer current session manifest
            curr_manifest = db_manager.get_cleaning_manifest(state.session_id)
            if curr_manifest:
                if st.checkbox("Use current session's recorded manifest", value=True):
                    manifest_to_replay = curr_manifest

        if manifest_to_replay:
            st.json(manifest_to_replay, expanded=False)
            if st.button("🚀 Replay Manifest Against Current Dataset", type="primary"):
                with st.spinner("Replaying manifest transformations..."):
                    try:
                        state.push_snapshot("Before manifest replay")
                        replayed_df, replay_logs = ReportExporter.replay_manifest(state.current_df, manifest_to_replay)
                        state.update_after_mutation(replayed_df, "Manifest replay")
                        state.logger.log("MANIFEST_REPLAYED", f"Successfully replayed {len(replay_logs)} operations.")
                        st.success("Manifest replay completed successfully!")
                        st.dataframe(pd.DataFrame(replay_logs), use_container_width=True)
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Replay halted: {str(ex)}")

"""Data Explorer UI for DataPilot AI."""

import streamlit as st
import pandas as pd
from agent.state import SessionState

def render_explorer(state: SessionState):
    """Render interactive data explorer and detailed column profiler."""
    st.markdown("## 🔎 Interactive Data Explorer")
    st.markdown("Explore dataset structure, examine column statistics, and inspect data distributions.")

    if state.current_df is None:
        st.info("No dataset currently loaded. Please upload a dataset in the Overview tab.")
        return

    df = state.current_df
    profile = state.current_profile
    cols_meta = profile.get("columns", {})

    tab_data, tab_columns, tab_corr, tab_missing = st.tabs([
        "📄 Raw Records", "📊 Column Profiles", "🔗 Correlation Matrix", "❓ Missing Value Map"
    ])

    with tab_data:
        st.markdown(f"**Viewing {len(df)} rows & {len(df.columns)} columns**")
        st.dataframe(df, use_container_width=True, height=450)

    with tab_columns:
        selected_col = st.selectbox("Select Column to Inspect:", options=list(df.columns))
        if selected_col and selected_col in cols_meta:
            cm = cols_meta[selected_col]
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(
                    f"<div class='datapilot-card'>"
                    f"<div class='metric-title'>Inferred Type</div>"
                    f"<div class='metric-value' style='font-size: 18px; color: #22D3EE;'>{cm.get('semantic_type', 'unknown').upper()}</div>"
                    f"<div class='metric-sub'>Raw dtype: {cm.get('raw_dtype')}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with c2:
                st.markdown(
                    f"<div class='datapilot-card'>"
                    f"<div class='metric-title'>Non-Null Count</div>"
                    f"<div class='metric-value'>{cm.get('non_null_count')}</div>"
                    f"<div class='metric-sub'>Nulls: {cm.get('null_count')} ({cm.get('null_rate', 0):.1%})</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with c3:
                st.markdown(
                    f"<div class='datapilot-card'>"
                    f"<div class='metric-title'>Distinct Values</div>"
                    f"<div class='metric-value'>{cm.get('unique_count')}</div>"
                    f"<div class='metric-sub'>Uniqueness: {cm.get('uniqueness_ratio', 0):.1%}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with c4:
                outliers = cm.get("outlier_info", {}).get("count", 0)
                st.markdown(
                    f"<div class='datapilot-card'>"
                    f"<div class='metric-title'>Outliers (1.5*IQR)</div>"
                    f"<div class='metric-value' style='color: {'#EF4444' if outliers > 0 else '#10B981'};'>{outliers}</div>"
                    f"<div class='metric-sub'>{cm.get('outlier_info', {}).get('outlier_rate', 0):.1%} of valid records</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

            # Details
            col_left, col_right = st.columns([1, 1])
            with col_left:
                if cm.get("stats"):
                    st.markdown("#### Numerical Summary")
                    stats_df = pd.DataFrame(list(cm["stats"].items()), columns=["Metric", "Value"])
                    st.dataframe(stats_df, use_container_width=True, hide_index=True)
                elif cm.get("top_values"):
                    st.markdown("#### Most Frequent Categories")
                    top_df = pd.DataFrame(list(cm["top_values"].items()), columns=["Category", "Frequency"])
                    st.dataframe(top_df, use_container_width=True, hide_index=True)

            with col_right:
                st.markdown("#### Column Quality Checks")
                issues = cm.get("issues", [])
                if issues:
                    for iss in issues:
                        st.warning(f"**{iss['type'].replace('_', ' ').title()}**: {iss['description']}")
                else:
                    st.success("✅ No data-quality anomalies detected for this column.")

    with tab_corr:
        corrs = profile.get("correlations", {})
        if corrs:
            corr_df = pd.DataFrame(corrs).round(3)
            st.dataframe(corr_df, use_container_width=True)
            import plotly.graph_objects as go
            fig_hm = go.Figure(data=go.Heatmap(
                z=corr_df.values,
                x=corr_df.columns,
                y=corr_df.index,
                colorscale="Viridis",
                zmin=-1, zmax=1,
                text=corr_df.values,
                texttemplate="%{text}",
                colorbar=dict(title="r")
            ))
            from data_engine.visualization import apply_chart_theme
            apply_chart_theme(fig_hm, "Correlation Heatmap")
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info("Insufficient numeric measures to compute a correlation matrix (requires >= 2 continuous/discrete numeric columns).")

    with tab_missing:
        missing_data = []
        for col, meta in cols_meta.items():
            if meta.get("null_count", 0) > 0:
                missing_data.append({
                    "Column": col,
                    "Type": meta.get("semantic_type"),
                    "Missing Count": meta.get("null_count"),
                    "Missing Percentage": f"{meta.get('null_rate', 0):.1%}"
                })
        if missing_data:
            st.dataframe(pd.DataFrame(missing_data), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Zero missing values across the entire dataset!")

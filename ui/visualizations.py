"""Visualizations UI for DataPilot AI."""

import streamlit as st
import pandas as pd
from agent.state import SessionState
from data_engine.visualization import VisualizationEngine

def render_visualizations(state: SessionState):
    """Render automated recommended charts and the custom chart builder."""
    st.markdown("## 📈 Interactive Visual Analytics")
    st.markdown("Inspect automatically synthesized data charts or construct custom interactive views.")

    if state.current_df is None:
        st.info("No active dataset. Please upload or load a sample dataset in the Overview tab.")
        return

    df = state.current_df
    profile = state.current_profile

    tab_auto, tab_custom = st.tabs(["✨ Recommended Charts", "🛠️ Custom Chart Builder"])

    with tab_auto:
        st.markdown("### Automatically Recommended Visualizations")
        st.caption("Heuristically selected based on inferred column types, cardinality, and data health.")

        recommended = VisualizationEngine.generate_recommended_charts(df, profile)
        if not recommended:
            st.info("No automatic chart patterns detected for the current dataset configuration.")
        else:
            for item in recommended:
                st.markdown(f"#### {item['title']}")
                st.caption(item.get("description", ""))
                st.plotly_chart(item["figure"], use_container_width=True)
                st.markdown("---")

    with tab_custom:
        st.markdown("### Custom Interactive Chart Studio")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            chart_type = st.selectbox(
                "Chart Type:",
                ["bar", "line", "scatter", "histogram", "box", "pie"],
                format_func=lambda x: x.title()
            )
        with c2:
            x_col = st.selectbox("X-Axis Column:", options=list(df.columns))
        with c3:
            y_col_options = ["None"] + list(df.columns)
            y_col = st.selectbox("Y-Axis Column (Optional):", options=y_col_options)

        c4, c5, c6 = st.columns(3)
        with c4:
            color_col_options = ["None"] + list(df.columns)
            color_col = st.selectbox("Color / Group Dimension:", options=color_col_options)
        with c5:
            agg_func = st.selectbox("Aggregation Method:", ["None", "mean", "sum", "median", "count"])
        with c6:
            chart_title = st.text_input("Chart Title (Optional):", "")

        if st.button("📊 Render Custom Chart", type="primary"):
            y_param = None if y_col == "None" else y_col
            color_param = None if color_col == "None" else color_col
            agg_param = None if agg_func == "None" else agg_func

            fig = VisualizationEngine.build_custom_chart(
                df,
                chart_type=chart_type,
                x_col=x_col,
                y_col=y_param,
                color_col=color_param,
                agg_func=agg_param,
                title=chart_title
            )

            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Could not construct chart with the chosen parameters. Check data types and selections.")

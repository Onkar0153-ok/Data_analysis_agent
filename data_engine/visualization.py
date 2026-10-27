"""Interactive Plotly Visualization Engine for DataPilot AI."""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from config.settings import THEME
from data_engine.profiler import SemanticType

logger = logging.getLogger(__name__)

# Dark theme palette for Plotly charts
COLOR_SEQUENCE = ["#22D3EE", "#60A5FA", "#A78BFA", "#34D399", "#F59E0B", "#F43F5E", "#E879F9"]

def apply_chart_theme(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply consistent premium dark analytics styling to Plotly figures."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family="Inter, Roboto, sans-serif", size=15, color=THEME["text_main"]),
            x=0.02,
            y=0.96,
        ),
        paper_bgcolor="rgba(20, 31, 50, 0.7)",
        plot_bgcolor="rgba(11, 18, 32, 0.8)",
        font=dict(family="Inter, Roboto, sans-serif", color=THEME["text_muted"], size=12),
        margin=dict(l=40, r=30, t=50, b=40),
        xaxis=dict(
            gridcolor=THEME["border"],
            zerolinecolor=THEME["border"],
            showline=True,
            linecolor=THEME["border"],
            tickfont=dict(color=THEME["text_muted"])
        ),
        yaxis=dict(
            gridcolor=THEME["border"],
            zerolinecolor=THEME["border"],
            showline=True,
            linecolor=THEME["border"],
            tickfont=dict(color=THEME["text_muted"])
        ),
        legend=dict(
            font=dict(color=THEME["text_main"]),
            bgcolor="rgba(17, 24, 39, 0.6)",
            bordercolor=THEME["border"]
        ),
        hoverlabel=dict(
            bgcolor=THEME["bg_card"],
            font_size=12,
            font_color=THEME["text_main"],
            bordercolor=THEME["accent_primary"]
        )
    )
    return fig

class VisualizationEngine:
    """Generates automated and custom interactive charts."""

    @staticmethod
    def generate_recommended_charts(df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Automatically select and build the most informative charts for the dataset."""
        recommended: List[Dict[str, Any]] = []
        if df is None or df.empty:
            return recommended

        columns_meta = profile.get("columns", {})
        
        # 1. Missing Values Overview Chart (if missing values exist)
        missing_data = {col: cinfo["null_rate"] * 100 for col, cinfo in columns_meta.items() if cinfo.get("null_count", 0) > 0}
        if missing_data:
            df_miss = pd.DataFrame(list(missing_data.items()), columns=["Column", "MissingPercentage"]).sort_values(by="MissingPercentage", ascending=True)
            fig_miss = px.bar(
                df_miss,
                x="MissingPercentage",
                y="Column",
                orientation="h",
                text="MissingPercentage",
                color_discrete_sequence=["#F59E0B"]
            )
            fig_miss.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            apply_chart_theme(fig_miss, "Missing Value Rates by Column (%)")
            recommended.append({
                "id": "missing_overview",
                "title": "Missing Values Overview",
                "type": "bar",
                "description": "Displays columns with incomplete data requiring attention.",
                "figure": fig_miss
            })

        # 2. Correlation Heatmap for Numeric Measures (excluding identifiers)
        valid_numeric = [
            col for col, cinfo in columns_meta.items()
            if cinfo.get("semantic_type") in [SemanticType.NUMERIC_CONTINUOUS, SemanticType.NUMERIC_DISCRETE]
            and cinfo.get("unique_count", 0) > 1
        ]
        if len(valid_numeric) >= 2:
            corr = df[valid_numeric].corr().round(2)
            fig_corr = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=corr.columns,
                y=corr.index,
                colorscale="Viridis",
                zmin=-1, zmax=1,
                text=corr.values,
                texttemplate="%{text}",
                colorbar=dict(title="r")
            ))
            apply_chart_theme(fig_corr, "Pairwise Correlation Matrix")
            recommended.append({
                "id": "correlation_heatmap",
                "title": "Correlation Matrix",
                "type": "heatmap",
                "description": "Linear correlation coefficients across numeric measures.",
                "figure": fig_corr
            })

        # 3. Categorical Distribution (Primary categorical feature)
        cat_cols = [
            col for col, cinfo in columns_meta.items()
            if cinfo.get("semantic_type") == SemanticType.CATEGORICAL
            and 2 <= cinfo.get("unique_count", 0) <= 20
        ]
        if cat_cols:
            primary_cat = cat_cols[0]
            top_counts = df[primary_cat].value_counts().head(10).reset_index()
            top_counts.columns = [primary_cat, "Count"]
            fig_cat = px.bar(
                top_counts,
                x=primary_cat,
                y="Count",
                color=primary_cat,
                color_discrete_sequence=COLOR_SEQUENCE
            )
            apply_chart_theme(fig_cat, f"Category Distribution: {primary_cat}")
            recommended.append({
                "id": f"cat_dist_{primary_cat}",
                "title": f"Distribution: {primary_cat}",
                "type": "bar",
                "description": f"Frequency distribution across '{primary_cat}' categories.",
                "figure": fig_cat
            })

        # 4. Numeric Measure Distribution (Histogram & Box)
        if valid_numeric:
            primary_num = valid_numeric[0]
            fig_hist = px.histogram(
                df,
                x=primary_num,
                marginal="box",
                nbins=30,
                color_discrete_sequence=["#22D3EE"]
            )
            apply_chart_theme(fig_hist, f"Distribution & Outlier Box: {primary_num}")
            recommended.append({
                "id": f"num_dist_{primary_num}",
                "title": f"Distribution: {primary_num}",
                "type": "histogram",
                "description": f"Histogram and box plot showing spread and skewness of '{primary_num}'.",
                "figure": fig_hist
            })

        # 5. Scatter Plot (if >= 2 numeric measures exist)
        if len(valid_numeric) >= 2:
            x_col = valid_numeric[0]
            y_col = valid_numeric[1]
            color_col = cat_cols[0] if cat_cols else None
            
            # Check if statsmodels is available for OLS trendlines
            try:
                import statsmodels.api  # noqa: F401
                has_statsmodels = True
            except (ImportError, Exception):
                has_statsmodels = False

            trendline_arg = "ols" if (has_statsmodels and len(df.dropna(subset=[x_col, y_col])) > 5) else None

            try:
                fig_scatter = px.scatter(
                    df,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    color_discrete_sequence=COLOR_SEQUENCE,
                    trendline=trendline_arg
                )
            except Exception:
                fig_scatter = px.scatter(
                    df,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    color_discrete_sequence=COLOR_SEQUENCE
                )

            apply_chart_theme(fig_scatter, f"{y_col} vs {x_col}")
            recommended.append({
                "id": f"scatter_{x_col}_{y_col}",
                "title": f"{y_col} vs {x_col}",
                "type": "scatter",
                "description": f"Relationship between {x_col} and {y_col}.",
                "figure": fig_scatter
            })

        # 6. Time Series Trend (if datetime column and numeric column exist)
        date_cols = [col for col, cinfo in columns_meta.items() if cinfo.get("semantic_type") == SemanticType.DATETIME]
        if date_cols and valid_numeric:
            date_col = date_cols[0]
            num_col = valid_numeric[0]
            try:
                df_temp = df.copy()
                df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")
                df_trend = df_temp.dropna(subset=[date_col, num_col]).sort_values(by=date_col)
                if not df_trend.empty:
                    fig_trend = px.line(
                        df_trend,
                        x=date_col,
                        y=num_col,
                        color_discrete_sequence=["#38BDF8"]
                    )
                    apply_chart_theme(fig_trend, f"Time Series Trend: {num_col} over {date_col}")
                    recommended.append({
                        "id": f"trend_{date_col}_{num_col}",
                        "title": f"Trend: {num_col} over Time",
                        "type": "line",
                        "description": f"Chronological trend of {num_col} over {date_col}.",
                        "figure": fig_trend
                    })
            except Exception as e:
                logger.warning("Error generating time series chart: %s", e)

        return recommended

    @staticmethod
    def build_custom_chart(
        df: pd.DataFrame,
        chart_type: str,
        x_col: str,
        y_col: Optional[str] = None,
        color_col: Optional[str] = None,
        agg_func: Optional[str] = None,
        title: Optional[str] = None
    ) -> Optional[go.Figure]:
        """Build custom user-configured Plotly chart."""
        if df is None or df.empty or not x_col:
            return None

        chart_type = chart_type.lower()
        custom_title = title or f"{chart_type.title()} Chart: {x_col}" + (f" vs {y_col}" if y_col else "")
        fig: Optional[go.Figure] = None

        try:
            # Handle aggregation if requested
            plot_df = df.copy()
            if agg_func and agg_func != "None" and y_col and y_col in plot_df.columns:
                group_cols = [x_col]
                if color_col and color_col in plot_df.columns and color_col != x_col:
                    group_cols.append(color_col)
                
                if agg_func == "mean":
                    plot_df = plot_df.groupby(group_cols, as_index=False)[y_col].mean()
                elif agg_func == "sum":
                    plot_df = plot_df.groupby(group_cols, as_index=False)[y_col].sum()
                elif agg_func == "median":
                    plot_df = plot_df.groupby(group_cols, as_index=False)[y_col].median()
                elif agg_func == "count":
                    plot_df = plot_df.groupby(group_cols, as_index=False)[y_col].count()

            if chart_type == "bar":
                fig = px.bar(
                    plot_df,
                    x=x_col,
                    y=y_col,
                    color=color_col if color_col != "None" else None,
                    color_discrete_sequence=COLOR_SEQUENCE,
                    barmode="group"
                )
            elif chart_type == "line":
                fig = px.line(
                    plot_df,
                    x=x_col,
                    y=y_col,
                    color=color_col if color_col != "None" else None,
                    color_discrete_sequence=COLOR_SEQUENCE,
                    markers=True
                )
            elif chart_type == "scatter":
                fig = px.scatter(
                    plot_df,
                    x=x_col,
                    y=y_col,
                    color=color_col if color_col != "None" else None,
                    color_discrete_sequence=COLOR_SEQUENCE
                )
            elif chart_type == "histogram":
                fig = px.histogram(
                    plot_df,
                    x=x_col,
                    y=y_col if y_col and y_col != "None" else None,
                    color=color_col if color_col != "None" else None,
                    color_discrete_sequence=COLOR_SEQUENCE,
                    marginal="box"
                )
            elif chart_type == "box":
                fig = px.box(
                    plot_df,
                    x=x_col,
                    y=y_col if y_col and y_col != "None" else None,
                    color=color_col if color_col != "None" else None,
                    color_discrete_sequence=COLOR_SEQUENCE
                )
            elif chart_type == "pie":
                # Ensure limited categories for readable pie chart
                top_pie = plot_df[x_col].value_counts().head(8).reset_index()
                top_pie.columns = [x_col, "Count"]
                fig = px.pie(
                    top_pie,
                    names=x_col,
                    values="Count",
                    color_discrete_sequence=COLOR_SEQUENCE,
                    hole=0.4
                )

            if fig:
                apply_chart_theme(fig, custom_title)
            return fig

        except Exception as e:
            logger.error("Error creating custom chart: %s", e)
            return None

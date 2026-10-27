"""Controlled Tool Execution Engine for DataPilot AI."""

import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from data_engine.visualization import VisualizationEngine

logger = logging.getLogger(__name__)

class ToolExecutor:
    """Executes validated analysis tools against the loaded Pandas dataset."""

    @staticmethod
    def execute_tool(
        tool_name: str,
        arguments: Dict[str, Any],
        df: pd.DataFrame,
        profile: Dict[str, Any],
        quality_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch and execute tool with safe input validation."""
        if df is None or df.empty:
            return {"success": False, "error": "No active dataset loaded."}

        try:
            if tool_name == "get_dataset_summary":
                return ToolExecutor._get_dataset_summary(df, profile)
            elif tool_name == "get_column_profile":
                return ToolExecutor._get_column_profile(df, profile, arguments.get("column_name"))
            elif tool_name == "get_missing_value_report":
                return ToolExecutor._get_missing_value_report(df, profile)
            elif tool_name == "get_duplicate_report":
                return ToolExecutor._get_duplicate_report(df, profile)
            elif tool_name == "get_top_bottom_values":
                return ToolExecutor._get_top_bottom_values(
                    df, arguments.get("column_name"), arguments.get("n", 5), arguments.get("order", "top")
                )
            elif tool_name == "calculate_aggregation":
                return ToolExecutor._calculate_aggregation(
                    df, arguments.get("group_by_column"), arguments.get("metric_column"), arguments.get("agg_func", "mean")
                )
            elif tool_name == "calculate_correlation":
                return ToolExecutor._calculate_correlation(df, arguments.get("col1"), arguments.get("col2"))
            elif tool_name == "detect_outliers":
                return ToolExecutor._detect_outliers(df, arguments.get("column_name"))
            elif tool_name == "filter_dataset":
                return ToolExecutor._filter_dataset(
                    df, arguments.get("column_name"), arguments.get("operator", "=="), arguments.get("value")
                )
            elif tool_name == "compare_groups":
                return ToolExecutor._compare_groups(df, arguments.get("group_column"), arguments.get("metric_column"))
            elif tool_name == "get_quality_report":
                return ToolExecutor._get_quality_report(quality_score, profile)
            elif tool_name == "create_chart":
                return ToolExecutor._create_chart(
                    df, arguments.get("chart_type"), arguments.get("x_column"), arguments.get("y_column"), arguments.get("title")
                )
            else:
                return {"success": False, "error": f"Unknown tool: '{tool_name}'"}

        except Exception as e:
            logger.exception("Error executing tool %s", tool_name)
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}

    @staticmethod
    def _find_column(df: pd.DataFrame, requested_name: Optional[str]) -> Optional[str]:
        """Case-insensitive column lookup with strip."""
        if not requested_name:
            return None
        req = str(requested_name).strip().lower()
        for col in df.columns:
            if col.strip().lower() == req:
                return col
        return None

    @staticmethod
    def _get_dataset_summary(df: pd.DataFrame, profile: Dict[str, Any]) -> Dict[str, Any]:
        columns_info = {
            col: {
                "dtype": str(df[col].dtype),
                "semantic_type": profile.get("columns", {}).get(col, {}).get("semantic_type", "unknown"),
                "null_count": int(df[col].isna().sum())
            }
            for col in df.columns
        }
        return {
            "success": True,
            "tool": "get_dataset_summary",
            "rows": len(df),
            "columns_count": len(df.columns),
            "total_missing_cells": int(df.isna().sum().sum()),
            "missing_rate": f"{profile.get('missing_rate', 0.0):.1%}",
            "duplicate_rows": int(df.duplicated().sum()),
            "columns": columns_info
        }

    @staticmethod
    def _get_column_profile(df: pd.DataFrame, profile: Dict[str, Any], column_name: Optional[str]) -> Dict[str, Any]:
        col = ToolExecutor._find_column(df, column_name)
        if not col:
            return {"success": False, "error": f"Column '{column_name}' not found. Available: {list(df.columns)}"}

        meta = profile.get("columns", {}).get(col, {})
        return {
            "success": True,
            "tool": "get_column_profile",
            "column": col,
            "dtype": str(df[col].dtype),
            "semantic_type": meta.get("semantic_type", "unknown"),
            "non_null_count": int(df[col].notna().sum()),
            "null_count": int(df[col].isna().sum()),
            "null_rate": f"{meta.get('null_rate', 0.0):.1%}",
            "unique_count": int(df[col].nunique()),
            "stats": meta.get("stats", {}),
            "top_values": meta.get("top_values", {})
        }

    @staticmethod
    def _get_missing_value_report(df: pd.DataFrame, profile: Dict[str, Any]) -> Dict[str, Any]:
        missing_dict = {}
        for col in df.columns:
            nulls = int(df[col].isna().sum())
            if nulls > 0:
                missing_dict[col] = {
                    "count": nulls,
                    "percentage": round((nulls / len(df)) * 100, 2)
                }
        return {
            "success": True,
            "tool": "get_missing_value_report",
            "total_missing_cells": int(df.isna().sum().sum()),
            "overall_missing_rate": f"{profile.get('missing_rate', 0.0):.1%}",
            "columns_with_missing": missing_dict
        }

    @staticmethod
    def _get_duplicate_report(df: pd.DataFrame, profile: Dict[str, Any]) -> Dict[str, Any]:
        dup_count = int(df.duplicated().sum())
        rate = dup_count / len(df) if len(df) > 0 else 0.0
        return {
            "success": True,
            "tool": "get_duplicate_report",
            "duplicate_rows": dup_count,
            "duplicate_rate": f"{rate:.1%}",
            "total_rows": len(df),
            "is_clean": dup_count == 0
        }

    @staticmethod
    def _get_top_bottom_values(df: pd.DataFrame, column_name: Optional[str], n: int = 5, order: str = "top") -> Dict[str, Any]:
        col = ToolExecutor._find_column(df, column_name)
        if not col:
            return {"success": False, "error": f"Column '{column_name}' not found."}

        n = max(1, min(int(n), 20))
        ascending = (order.lower() == "bottom")
        
        # Sort and take head
        s_clean = df.dropna(subset=[col])
        sorted_df = s_clean.sort_values(by=col, ascending=ascending).head(n)
        
        records = sorted_df.to_dict(orient="records")
        return {
            "success": True,
            "tool": "get_top_bottom_values",
            "column": col,
            "order": order,
            "count": len(records),
            "records": records
        }

    @staticmethod
    def _calculate_aggregation(df: pd.DataFrame, group_col: Optional[str], metric_col: Optional[str], agg_func: str = "mean") -> Dict[str, Any]:
        gcol = ToolExecutor._find_column(df, group_col)
        mcol = ToolExecutor._find_column(df, metric_col)
        if not gcol:
            return {"success": False, "error": f"Group column '{group_col}' not found."}
        if not mcol:
            return {"success": False, "error": f"Metric column '{metric_col}' not found."}

        # Check numeric
        if not pd.api.types.is_numeric_dtype(df[mcol]):
            return {"success": False, "error": f"Metric column '{mcol}' must be numeric (found: {df[mcol].dtype})."}

        agg_func = agg_func.lower()
        if agg_func not in ["mean", "sum", "median", "count", "min", "max"]:
            agg_func = "mean"

        agg_df = df.groupby(gcol)[mcol].agg(agg_func).round(2).reset_index()
        agg_df.columns = [gcol, f"{agg_func}_{mcol}"]
        # Sort by value descending
        agg_df = agg_df.sort_values(by=f"{agg_func}_{mcol}", ascending=False)

        results = dict(zip(agg_df[gcol].astype(str), agg_df[f"{agg_func}_{mcol}"]))
        top_group = agg_df.iloc[0][gcol] if not agg_df.empty else None
        top_val = agg_df.iloc[0][f"{agg_func}_{mcol}"] if not agg_df.empty else None

        return {
            "success": True,
            "tool": "calculate_aggregation",
            "group_column": gcol,
            "metric_column": mcol,
            "agg_func": agg_func,
            "results": results,
            "top_group": str(top_group),
            "top_value": float(top_val) if top_val is not None else None,
            "table": agg_df.to_dict(orient="records")
        }

    @staticmethod
    def _calculate_correlation(df: pd.DataFrame, col1_name: Optional[str], col2_name: Optional[str]) -> Dict[str, Any]:
        c1 = ToolExecutor._find_column(df, col1_name)
        c2 = ToolExecutor._find_column(df, col2_name)
        if not c1 or not c2:
            return {"success": False, "error": f"Columns '{col1_name}' and/or '{col2_name}' not found."}

        if not pd.api.types.is_numeric_dtype(df[c1]) or not pd.api.types.is_numeric_dtype(df[c2]):
            return {"success": False, "error": "Both columns must be numeric to calculate correlation."}

        clean_sub = df[[c1, c2]].dropna()
        if len(clean_sub) < 3:
            return {"success": False, "error": "Insufficient non-null rows to compute correlation."}

        corr = round(float(clean_sub[c1].corr(clean_sub[c2])), 4)
        
        # Interpret correlation
        if abs(corr) >= 0.7:
            strength = "strong"
        elif abs(corr) >= 0.4:
            strength = "moderate"
        elif abs(corr) >= 0.2:
            strength = "weak"
        else:
            strength = "negligible"

        direction = "positive" if corr > 0 else "negative"

        return {
            "success": True,
            "tool": "calculate_correlation",
            "col1": c1,
            "col2": c2,
            "correlation": corr,
            "interpretation": f"{strength} {direction} linear relationship (r = {corr})"
        }

    @staticmethod
    def _detect_outliers(df: pd.DataFrame, column_name: Optional[str]) -> Dict[str, Any]:
        col = ToolExecutor._find_column(df, column_name)
        if not col or not pd.api.types.is_numeric_dtype(df[col]):
            return {"success": False, "error": f"Numeric column '{column_name}' not found."}

        s = df[col].dropna()
        q25 = float(s.quantile(0.25))
        q75 = float(s.quantile(0.75))
        iqr = q75 - q25
        lower = q25 - 1.5 * iqr
        upper = q75 + 1.5 * iqr

        outliers = s[(s < lower) | (s > upper)]
        return {
            "success": True,
            "tool": "detect_outliers",
            "column": col,
            "outlier_count": len(outliers),
            "outlier_rate": f"{len(outliers) / len(s):.1%}",
            "bounds": {"lower": round(lower, 2), "upper": round(upper, 2)},
            "sample_outlier_values": [round(float(v), 2) for v in outliers.head(5).tolist()]
        }

    @staticmethod
    def _filter_dataset(df: pd.DataFrame, column_name: Optional[str], operator: str, value: Any) -> Dict[str, Any]:
        col = ToolExecutor._find_column(df, column_name)
        if not col:
            return {"success": False, "error": f"Column '{column_name}' not found."}

        try:
            val = float(value) if pd.api.types.is_numeric_dtype(df[col]) else str(value).strip()
            if operator == ">":
                mask = df[col] > val
            elif operator == "<":
                mask = df[col] < val
            elif operator == ">=":
                mask = df[col] >= val
            elif operator == "<=":
                mask = df[col] <= val
            elif operator == "==":
                mask = (df[col] == val) if not isinstance(val, str) else (df[col].astype(str).str.lower() == val.lower())
            elif operator == "!=":
                mask = df[col] != val
            else:
                return {"success": False, "error": f"Unsupported operator '{operator}'"}

            matching = int(mask.sum())
            return {
                "success": True,
                "tool": "filter_dataset",
                "condition": f"{col} {operator} {value}",
                "matching_rows": matching,
                "matching_percentage": f"{(matching / len(df)) * 100:.1f}%",
                "total_rows": len(df)
            }
        except Exception as e:
            return {"success": False, "error": f"Filter error: {str(e)}"}

    @staticmethod
    def _compare_groups(df: pd.DataFrame, group_col: Optional[str], metric_col: Optional[str]) -> Dict[str, Any]:
        gcol = ToolExecutor._find_column(df, group_col)
        mcol = ToolExecutor._find_column(df, metric_col)
        if not gcol or not mcol or not pd.api.types.is_numeric_dtype(df[mcol]):
            return {"success": False, "error": "Invalid columns for group comparison."}

        stats_df = df.groupby(gcol)[mcol].agg(["count", "mean", "median", "std"]).round(2).reset_index()
        return {
            "success": True,
            "tool": "compare_groups",
            "group_column": gcol,
            "metric_column": mcol,
            "groups": stats_df.to_dict(orient="records")
        }

    @staticmethod
    def _get_quality_report(quality_score: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "success": True,
            "tool": "get_quality_report",
            "overall_score": quality_score.get("overall_score", 0.0),
            "grade": quality_score.get("grade", "N/A"),
            "breakdown": quality_score.get("breakdown", {}),
            "issues_count": len(profile.get("issues", [])),
            "explanation": quality_score.get("explanation", "")
        }

    @staticmethod
    def _create_chart(df: pd.DataFrame, chart_type: Optional[str], x_col: Optional[str], y_col: Optional[str], title: Optional[str]) -> Dict[str, Any]:
        x = ToolExecutor._find_column(df, x_col)
        y = ToolExecutor._find_column(df, y_col) if y_col else None
        if not x:
            return {"success": False, "error": f"Column '{x_col}' not found."}

        fig = VisualizationEngine.build_custom_chart(
            df, chart_type=chart_type or "bar", x_col=x, y_col=y, title=title
        )
        if fig:
            return {
                "success": True,
                "tool": "create_chart",
                "chart_type": chart_type,
                "x_column": x,
                "y_column": y,
                "figure": fig,
                "message": f"Generated {chart_type} chart for '{x}'" + (f" and '{y}'" if y else "")
            }
        return {"success": False, "error": "Could not generate requested chart."}

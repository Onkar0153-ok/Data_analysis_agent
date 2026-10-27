"""Deterministic Fallback Query Parser for No-Key Offline Mode."""

import re
import logging
from typing import Dict, Any, Optional
import pandas as pd

from llm.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)

class FallbackParser:
    """Parses natural-language data questions using keyword and pattern extraction when no LLM key is configured."""

    @staticmethod
    def answer_question(
        question: str,
        df: pd.DataFrame,
        profile: Dict[str, Any],
        quality_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Attempt to route question to the appropriate tool and produce an answer."""
        q = question.lower().strip()
        matched_tool = None
        tool_args = {}
        explanation = ""

        cols_lower = {col.lower(): col for col in df.columns}

        # 1. Summary / Overview / Dimensions
        if any(w in q for w in ["summary", "overview", "shape", "dimensions", "how many rows", "dataset info"]):
            matched_tool = "get_dataset_summary"
            res = ToolExecutor.execute_tool(matched_tool, {}, df, profile, quality_score)
            explanation = (
                f"**Dataset Summary:**\n"
                f"- Records: **{res.get('rows')}** rows\n"
                f"- Columns: **{res.get('columns_count')}**\n"
                f"- Missing Values: **{res.get('total_missing_cells')}** cells ({res.get('missing_rate')})\n"
                f"- Duplicates: **{res.get('duplicate_rows')}** rows\n"
                f"- Columns: {', '.join(df.columns)}"
            )
            return {"success": True, "answer": explanation, "tool": matched_tool, "raw_result": res}

        # 2. Missing Values
        if any(w in q for w in ["missing", "null", "nan", "empty cell"]):
            matched_tool = "get_missing_value_report"
            res = ToolExecutor.execute_tool(matched_tool, {}, df, profile, quality_score)
            cols_miss = res.get("columns_with_missing", {})
            if cols_miss:
                lines = [f"- **{c}**: {data['count']} missing ({data['percentage']}%)" for c, data in cols_miss.items()]
                explanation = f"**Missing Values Report:**\nTotal missing cells: **{res.get('total_missing_cells')}** ({res.get('overall_missing_rate')})\n" + "\n".join(lines)
            else:
                explanation = "✅ No missing values detected in any column of the dataset!"
            return {"success": True, "answer": explanation, "tool": matched_tool, "raw_result": res}

        # 3. Duplicate Rows
        if any(w in q for w in ["duplicate", "duplicates", "duplicated"]):
            matched_tool = "get_duplicate_report"
            res = ToolExecutor.execute_tool(matched_tool, {}, df, profile, quality_score)
            dups = res.get("duplicate_rows", 0)
            if dups > 0:
                explanation = f"⚠️ Dataset contains **{dups}** exact duplicate row(s) ({res.get('duplicate_rate')})."
            else:
                explanation = "✅ Zero duplicate rows detected in the dataset."
            return {"success": True, "answer": explanation, "tool": matched_tool, "raw_result": res}

        # 4. Data Quality Score
        if any(w in q for w in ["quality", "score", "grade", "health"]):
            matched_tool = "get_quality_report"
            res = ToolExecutor.execute_tool(matched_tool, {}, df, profile, quality_score)
            score = res.get("overall_score")
            grade = res.get("grade")
            explanation = (
                f"**DataPilot Quality Score:** **{score}/100** (Grade **{grade}**)\n\n"
                f"{res.get('explanation')}"
            )
            return {"success": True, "answer": explanation, "tool": matched_tool, "raw_result": res}

        # 5. Outliers
        if any(w in q for w in ["outlier", "outliers", "anomaly", "anomalies", "extreme value"]):
            # Check if specific column mentioned
            found_col = None
            for cl, orig_c in cols_lower.items():
                if cl in q:
                    found_col = orig_c
                    break
            if not found_col:
                # Pick first numeric column
                numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
                found_col = numeric_cols[0] if numeric_cols else None

            if found_col:
                matched_tool = "detect_outliers"
                res = ToolExecutor.execute_tool(matched_tool, {"column_name": found_col}, df, profile, quality_score)
                count = res.get("outlier_count", 0)
                bounds = res.get("bounds", {})
                explanation = (
                    f"**Outlier Analysis for '{found_col}':**\n"
                    f"- Detected: **{count}** statistical outlier(s) ({res.get('outlier_rate')})\n"
                    f"- 1.5*IQR Valid Range: [{bounds.get('lower')}, {bounds.get('upper')}]\n"
                    f"- Sample outlier values: {res.get('sample_outlier_values', [])}"
                )
                return {"success": True, "answer": explanation, "tool": matched_tool, "raw_result": res}

        # 6. Correlation
        if any(w in q for w in ["correlation", "relationship", "correlate", "related"]):
            found_cols = [orig_c for cl, orig_c in cols_lower.items() if cl in q and pd.api.types.is_numeric_dtype(df[orig_c])]
            if len(found_cols) >= 2:
                matched_tool = "calculate_correlation"
                res = ToolExecutor.execute_tool(matched_tool, {"col1": found_cols[0], "col2": found_cols[1]}, df, profile, quality_score)
                explanation = (
                    f"**Correlation Analysis:**\n"
                    f"The correlation between **{found_cols[0]}** and **{found_cols[1]}** is **r = {res.get('correlation')}**.\n"
                    f"Interpretation: {res.get('interpretation')}."
                )
                return {"success": True, "answer": explanation, "tool": matched_tool, "raw_result": res}

        # 7. Aggregation (e.g. "average revenue by region", "top category by sales", "total units per category")
        agg_keywords = {"average": "mean", "avg": "mean", "mean": "mean", "sum": "sum", "total": "sum", "highest": "mean", "lowest": "mean", "max": "max", "min": "min"}
        found_agg = "mean"
        for kw, func in agg_keywords.items():
            if kw in q:
                found_agg = func
                break

        # Check for group-by keywords: "by", "per", "across"
        if any(sep in q for sep in [" by ", " per ", " across "]):
            # Find candidate categorical and numeric columns
            found_numeric = None
            found_cat = None
            for cl, orig_c in cols_lower.items():
                if cl in q:
                    if pd.api.types.is_numeric_dtype(df[orig_c]) and not found_numeric:
                        found_numeric = orig_c
                    elif not pd.api.types.is_numeric_dtype(df[orig_c]) and not found_cat:
                        found_cat = orig_c

            if found_numeric and found_cat:
                matched_tool = "calculate_aggregation"
                res = ToolExecutor.execute_tool(
                    matched_tool,
                    {"group_by_column": found_cat, "metric_column": found_numeric, "agg_func": found_agg},
                    df, profile, quality_score
                )
                top_grp = res.get("top_group")
                top_val = res.get("top_value")
                explanation = (
                    f"**{found_agg.title()} of '{found_numeric}' by '{found_cat}':**\n\n"
                    f"The group with the highest {found_agg} is **{top_grp}** with **{top_val}**.\n\n"
                )
                for grp, val in res.get("results", {}).items():
                    explanation += f"- {grp}: **{val}**\n"
                
                # Also attach a bar chart!
                chart_res = ToolExecutor.execute_tool(
                    "create_chart",
                    {"chart_type": "bar", "x_column": found_cat, "y_column": found_numeric, "title": f"{found_agg.title()} {found_numeric} by {found_cat}"},
                    df, profile, quality_score
                )
                return {
                    "success": True,
                    "answer": explanation,
                    "tool": matched_tool,
                    "raw_result": res,
                    "chart": chart_res.get("figure")
                }

        # 8. Top / Bottom N records
        if any(w in q for w in ["top", "highest", "most", "bottom", "lowest", "least"]):
            order = "bottom" if any(w in q for w in ["bottom", "lowest", "least"]) else "top"
            # Extract number if present
            num_match = re.search(r'\b(\d+)\b', q)
            n_val = int(num_match.group(1)) if num_match else 5
            found_col = None
            for cl, orig_c in cols_lower.items():
                if cl in q and pd.api.types.is_numeric_dtype(df[orig_c]):
                    found_col = orig_c
                    break
            if not found_col:
                numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
                found_col = numeric_cols[0] if numeric_cols else None

            if found_col:
                matched_tool = "get_top_bottom_values"
                res = ToolExecutor.execute_tool(matched_tool, {"column_name": found_col, "n": n_val, "order": order}, df, profile, quality_score)
                explanation = f"**{order.title()} {n_val} records sorted by '{found_col}':**\n"
                for i, r in enumerate(res.get("records", []), 1):
                    explanation += f"{i}. {found_col}: **{r.get(found_col)}** (Order: {r.get('Order_ID', i)})\n"
                return {"success": True, "answer": explanation, "tool": matched_tool, "raw_result": res}

        # 9. Chart request
        if any(w in q for w in ["chart", "plot", "histogram", "graph", "visualize"]):
            ctype = "histogram" if "histogram" in q else ("scatter" if "scatter" in q else "bar")
            found_x = None
            found_y = None
            for cl, orig_c in cols_lower.items():
                if cl in q:
                    if not found_x:
                        found_x = orig_c
                    elif not found_y:
                        found_y = orig_c
            if found_x:
                matched_tool = "create_chart"
                res = ToolExecutor.execute_tool(
                    matched_tool,
                    {"chart_type": ctype, "x_column": found_x, "y_column": found_y, "title": f"{ctype.title()} of {found_x}"},
                    df, profile, quality_score
                )
                if res.get("success"):
                    return {
                        "success": True,
                        "answer": f"Generated interactive {ctype} chart for **{found_x}**" + (f" and **{found_y}**" if found_y else "") + ".",
                        "tool": matched_tool,
                        "raw_result": res,
                        "chart": res.get("figure")
                    }

        # If not recognized by fallback parser
        return {
            "success": False,
            "answer": (
                "🤖 **Offline Fallback Parser Notice:**\n"
                "I could not confidently extract a deterministic query for your prompt.\n\n"
                "Try phrasing like:\n"
                "- *'Give me a summary of this dataset'*\n"
                "- *'Which columns have missing values?'*\n"
                "- *'Average revenue by region'*\n"
                "- *'Top 5 products by units'*\n"
                "- *'What is the correlation between price and revenue?'*\n"
                "- *'Detect outliers in units'*\n"
                "- *'What is the data quality score?'*\n\n"
                "*For free-form natural language reasoning and custom questions, configure a Google Gemini API key in Settings.*"
            ),
            "tool": None,
            "raw_result": None
        }

"""Before-and-After Comparison Module for DataPilot AI."""

from typing import Dict, Any, List
import pandas as pd

class ComparisonEngine:
    """Calculates granular before-and-after metrics between original and cleaned states."""

    @staticmethod
    def compare_states(
        original_df: pd.DataFrame,
        current_df: pd.DataFrame,
        original_profile: Dict[str, Any],
        current_profile: Dict[str, Any],
        original_score: Dict[str, Any],
        current_score: Dict[str, Any],
        activity_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Produce structured comparison between original dataset and current cleaned dataset."""

        # Dimensions
        orig_rows = len(original_df) if original_df is not None else 0
        orig_cols = len(original_df.columns) if original_df is not None else 0
        curr_rows = len(current_df) if current_df is not None else 0
        curr_cols = len(current_df.columns) if current_df is not None else 0

        # Quality Scores
        score_before = original_score.get("overall_score", 0.0)
        score_after = current_score.get("overall_score", 0.0)
        score_delta = round(score_after - score_before, 1)

        # Missing values
        miss_before = original_profile.get("missing_cells", 0)
        miss_after = current_profile.get("missing_cells", 0)
        miss_rate_before = original_profile.get("missing_rate", 0.0)
        miss_rate_after = current_profile.get("missing_rate", 0.0)

        # Duplicates
        dup_before = original_profile.get("duplicate_rows", 0)
        dup_after = current_profile.get("duplicate_rows", 0)

        # Issues
        issues_before = len(original_profile.get("issues", []))
        issues_after = len(current_profile.get("issues", []))

        # Operation counts from activity logs
        completed_ops = sum(1 for log in activity_logs if log.get("status") == "PASSED" or log.get("status") == "SUCCESS")
        rolled_back = sum(1 for log in activity_logs if "ROLLBACK" in str(log.get("status", "")).upper() or "FAILED" in str(log.get("status", "")).upper())
        skipped_ops = sum(1 for log in activity_logs if "SKIPPED" in str(log.get("status", "")).upper() or "REJECTED" in str(log.get("status", "")).upper())

        # Column-by-column comparison table
        col_comparison = []
        all_cols = sorted(list(set(list(original_df.columns) + list(current_df.columns))))
        orig_meta = original_profile.get("columns", {})
        curr_meta = current_profile.get("columns", {})

        for col in all_cols:
            in_orig = col in original_df.columns
            in_curr = col in current_df.columns
            
            c_orig_miss = orig_meta.get(col, {}).get("null_count", "-") if in_orig else "N/A (Added)"
            c_curr_miss = curr_meta.get(col, {}).get("null_count", "-") if in_curr else "Dropped"

            c_orig_type = orig_meta.get(col, {}).get("raw_dtype", "-") if in_orig else "-"
            c_curr_type = curr_meta.get(col, {}).get("raw_dtype", "-") if in_curr else "-"

            col_comparison.append({
                "Column": col,
                "In Original": "Yes" if in_orig else "No",
                "In Cleaned": "Yes" if in_curr else "No (Dropped)",
                "Original Nulls": c_orig_miss,
                "Cleaned Nulls": c_curr_miss,
                "Original Dtype": c_orig_type,
                "Cleaned Dtype": c_curr_type,
            })

        df_col_comp = pd.DataFrame(col_comparison)

        return {
            "rows_before": orig_rows,
            "rows_after": curr_rows,
            "rows_diff": curr_rows - orig_rows,
            "cols_before": orig_cols,
            "cols_after": curr_cols,
            "cols_diff": curr_cols - orig_cols,
            "score_before": score_before,
            "score_after": score_after,
            "score_delta": score_delta,
            "grade_before": original_score.get("grade", "N/A"),
            "grade_after": current_score.get("grade", "N/A"),
            "missing_before": miss_before,
            "missing_after": miss_after,
            "missing_rate_before": miss_rate_before,
            "missing_rate_after": miss_rate_after,
            "duplicates_before": dup_before,
            "duplicates_after": dup_after,
            "issues_before": issues_before,
            "issues_after": issues_after,
            "completed_ops": completed_ops,
            "rolled_back_ops": rolled_back,
            "skipped_ops": skipped_ops,
            "column_comparison_df": df_col_comp,
            "remaining_issues": current_profile.get("issues", [])
        }

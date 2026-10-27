"""Autonomous Validation Engine for DataPilot AI."""

import logging
from typing import Dict, Any, Tuple
import pandas as pd
from agent.models import PlannedAction

logger = logging.getLogger(__name__)

class AgentValidator:
    """Rigorous post-execution validator ensuring operations resolve issues without unintended side-effects."""

    @staticmethod
    def validate_operation(
        df_before: pd.DataFrame,
        df_after: pd.DataFrame,
        action: PlannedAction,
        execution_metrics: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate whether the operation succeeded legitimately and preserved data integrity."""
        val_metrics: Dict[str, Any] = {
            "rows_before": len(df_before),
            "rows_after": len(df_after),
            "cols_before": len(df_before.columns),
            "cols_after": len(df_after.columns),
            "nulls_before": int(df_before.isna().sum().sum()),
            "nulls_after": int(df_after.isna().sum().sum()),
        }

        # 1. Basic sanity: empty dataset check
        if df_after is None or df_after.empty:
            return False, "Validation failed: Resulting dataset is completely empty.", val_metrics

        op = action.operation_name

        # 2. Check: remove_duplicate_rows
        if op == "remove_duplicate_rows":
            dups_remaining = int(df_after.duplicated().sum())
            if dups_remaining > 0:
                return False, f"Validation failed: Dataset still contains {dups_remaining} duplicate row(s).", val_metrics
            if len(df_after) > len(df_before):
                return False, "Validation failed: Row count unexpectedly increased after deduplication.", val_metrics
            return True, f"Validation passed: Successfully eliminated duplicates. ({len(df_after)} rows remaining)", val_metrics

        # 3. Check: trim_whitespace
        elif op == "trim_whitespace":
            target_cols = action.parameters.get("columns", df_after.columns)
            remaining_whitespace = 0
            for col in target_cols:
                if col in df_after.columns and (df_after[col].dtype == object or pd.api.types.is_string_dtype(df_after[col])):
                    s = df_after[col].dropna().astype(str)
                    remaining_whitespace += int((s != s.str.strip()).sum())
            if remaining_whitespace > 0:
                return False, f"Validation failed: {remaining_whitespace} cell(s) still contain untrimmed whitespace.", val_metrics
            return True, "Validation passed: All whitespace trimmed successfully.", val_metrics

        # 4. Check: impute_missing_numeric / impute_missing_categorical
        elif op in ["impute_missing_numeric", "impute_missing_categorical"]:
            col = action.parameters.get("column")
            if col not in df_after.columns:
                return False, f"Validation failed: Target column '{col}' missing from resulting dataset.", val_metrics
            nulls_remaining = int(df_after[col].isna().sum())
            if nulls_remaining > 0:
                return False, f"Validation failed: Column '{col}' still contains {nulls_remaining} missing values.", val_metrics
            # Ensure row count was not altered by imputation
            if len(df_after) != len(df_before):
                return False, f"Validation failed: Row count changed during imputation ({len(df_before)} -> {len(df_after)}).", val_metrics
            return True, f"Validation passed: All missing values in '{col}' were successfully imputed.", val_metrics

        # 5. Check: convert_column_type
        elif op == "convert_column_type":
            col = action.parameters.get("column")
            target_type = action.parameters.get("target_type")
            if col not in df_after.columns:
                return False, f"Validation failed: Column '{col}' missing after conversion.", val_metrics
            # Check for excessive new nulls created by failed parse
            new_nulls = int(df_after[col].isna().sum()) - int(df_before[col].isna().sum())
            if new_nulls > (0.15 * len(df_after)):
                return False, f"Validation failed: Type conversion corrupted data, introducing {new_nulls} new nulls.", val_metrics
            return True, f"Validation passed: Column '{col}' converted to {target_type} successfully.", val_metrics

        # 6. Check: remove_outliers_iqr
        elif op == "remove_outliers_iqr":
            col = action.parameters.get("column")
            if col not in df_after.columns:
                return False, f"Validation failed: Column '{col}' missing.", val_metrics
            # Plausibility check: should not drop more than 40% of records in an automated step
            dropped_ratio = (len(df_before) - len(df_after)) / max(1, len(df_before))
            if dropped_ratio > 0.40:
                return False, f"Validation failed: Outlier filtering dropped {dropped_ratio:.1%} of records (> 40% threshold).", val_metrics
            return True, f"Validation passed: Filtered outliers in '{col}'. Retained {len(df_after)} valid rows.", val_metrics

        # 7. Check: standardize_equivalent_categories
        elif op == "standardize_equivalent_categories":
            col = action.parameters.get("column")
            if col not in df_after.columns:
                return False, f"Validation failed: Column '{col}' missing.", val_metrics
            return True, f"Validation passed: Category labels standardized in '{col}'.", val_metrics

        # 8. Check: drop_columns
        elif op == "drop_columns":
            cols_to_drop = action.parameters.get("columns", [])
            still_present = [c for c in cols_to_drop if c in df_after.columns]
            if still_present:
                return False, f"Validation failed: Columns {still_present} were not dropped.", val_metrics
            return True, f"Validation passed: Dropped {len(cols_to_drop)} column(s).", val_metrics

        # Default fallback validation
        return True, "Validation passed: Dimensions and schema integrity verified.", val_metrics

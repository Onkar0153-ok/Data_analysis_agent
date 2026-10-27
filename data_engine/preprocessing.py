"""Data Preprocessing and Transformation Engine for DataPilot AI."""

import logging
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class PreprocessingEngine:
    """Predefined, deterministic data cleaning and transformation operations with safety guards."""

    @staticmethod
    def remove_duplicate_rows(df: pd.DataFrame, subset: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Remove exact duplicate rows."""
        df_new = df.copy()
        before_rows = len(df_new)
        df_new = df_new.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
        after_rows = len(df_new)
        removed = before_rows - after_rows
        return df_new, {
            "operation": "remove_duplicate_rows",
            "rows_before": before_rows,
            "rows_after": after_rows,
            "removed_rows": removed,
            "impact": f"Removed {removed} duplicate row(s)."
        }

    @staticmethod
    def trim_whitespace(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Trim leading and trailing whitespace from string columns."""
        df_new = df.copy()
        target_cols = columns or [c for c in df_new.columns if df_new[c].dtype == object or pd.api.types.is_string_dtype(df_new[c])]
        modified_count = 0
        cells_trimmed = 0

        for col in target_cols:
            if col in df_new.columns:
                s = df_new[col].astype(str)
                trimmed = s.str.strip()
                diff_mask = (s != trimmed) & df_new[col].notna()
                count = int(diff_mask.sum())
                if count > 0:
                    df_new[col] = df_new[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
                    modified_count += 1
                    cells_trimmed += count

        return df_new, {
            "operation": "trim_whitespace",
            "columns_affected": modified_count,
            "cells_trimmed": cells_trimmed,
            "impact": f"Trimmed whitespace in {cells_trimmed} cell(s) across {modified_count} column(s)."
        }

    @staticmethod
    def normalize_text_case(df: pd.DataFrame, columns: List[str], case_style: str = "title") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Normalize text casing (title, lower, upper)."""
        df_new = df.copy()
        cells_affected = 0
        for col in columns:
            if col in df_new.columns:
                def transform_case(val):
                    if not isinstance(val, str):
                        return val
                    if case_style == "lower":
                        return val.lower()
                    elif case_style == "upper":
                        return val.upper()
                    elif case_style == "title":
                        return val.title()
                    return val

                s_orig = df_new[col].copy()
                df_new[col] = df_new[col].apply(transform_case)
                cells_affected += int((s_orig != df_new[col]).sum())

        return df_new, {
            "operation": "normalize_text_case",
            "columns": columns,
            "case_style": case_style,
            "cells_affected": cells_affected,
            "impact": f"Normalized case to '{case_style}' in {cells_affected} cell(s)."
        }

    @staticmethod
    def standardize_equivalent_categories(df: pd.DataFrame, column: str, mapping: Optional[Dict[str, str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Standardize equivalent or typo categorical labels."""
        df_new = df.copy()
        if column not in df_new.columns:
            return df_new, {"operation": "standardize_equivalent_categories", "status": "skipped", "reason": f"Column '{column}' not found"}

        # If mapping is not provided, automatically generate case-standardized mapping to title/mode
        if not mapping:
            s_clean = df_new[column].dropna().astype(str).str.strip()
            # Map each case variant to the most frequent variant or Title case
            mode_per_lower = {}
            for val, count in s_clean.value_counts().items():
                low = val.lower()
                if low not in mode_per_lower:
                    mode_per_lower[low] = val
            mapping = {v: mode_per_lower[v.lower()] for v in s_clean.unique() if v != mode_per_lower[v.lower()]}

        s_orig = df_new[column].copy()
        df_new[column] = df_new[column].replace(mapping)
        changed_count = int((s_orig != df_new[column]).sum())

        return df_new, {
            "operation": "standardize_equivalent_categories",
            "column": column,
            "mapping": mapping,
            "labels_standardized": changed_count,
            "impact": f"Standardized {changed_count} entry/entries in '{column}' using mapping."
        }

    @staticmethod
    def impute_missing_numeric(df: pd.DataFrame, column: str, strategy: str = "median", fill_value: Optional[float] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Impute missing numerical values using mean, median, or constant."""
        df_new = df.copy()
        if column not in df_new.columns:
            return df_new, {"operation": "impute_missing_numeric", "status": "failed", "reason": "Column not found"}

        null_count = int(df_new[column].isna().sum())
        if null_count == 0:
            return df_new, {"operation": "impute_missing_numeric", "status": "skipped", "null_count": 0, "impact": "No missing values to impute"}

        s = pd.to_numeric(df_new[column], errors="coerce")
        if strategy == "median":
            val = float(s.median()) if not s.dropna().empty else 0.0
        elif strategy == "mean":
            val = float(s.mean()) if not s.dropna().empty else 0.0
        elif strategy == "constant":
            val = float(fill_value if fill_value is not None else 0.0)
        else:
            val = float(s.median())

        val = round(val, 2)
        df_new[column] = df_new[column].fillna(val)

        return df_new, {
            "operation": "impute_missing_numeric",
            "column": column,
            "strategy": strategy,
            "imputed_value": val,
            "imputed_count": null_count,
            "impact": f"Imputed {null_count} missing values in '{column}' with {strategy} ({val})."
        }

    @staticmethod
    def impute_missing_categorical(df: pd.DataFrame, column: str, strategy: str = "mode", fill_value: str = "Unknown") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Impute missing categorical values with mode or constant label."""
        df_new = df.copy()
        if column not in df_new.columns:
            return df_new, {"operation": "impute_missing_categorical", "status": "failed", "reason": "Column not found"}

        null_count = int(df_new[column].isna().sum())
        if null_count == 0:
            return df_new, {"operation": "impute_missing_categorical", "status": "skipped", "null_count": 0, "impact": "No missing values to impute"}

        if strategy == "mode":
            mode_s = df_new[column].mode(dropna=True)
            val = str(mode_s.iloc[0]) if not mode_s.empty else "Unknown"
        else:
            val = fill_value or "Unknown"

        df_new[column] = df_new[column].fillna(val)

        return df_new, {
            "operation": "impute_missing_categorical",
            "column": column,
            "strategy": strategy,
            "imputed_value": val,
            "imputed_count": null_count,
            "impact": f"Imputed {null_count} missing entries in '{column}' with '{val}'."
        }

    @staticmethod
    def drop_missing(df: pd.DataFrame, axis: str = "rows", subset: Optional[List[str]] = None, thresh: Optional[float] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Drop rows or columns with missing values."""
        df_new = df.copy()
        before_shape = df_new.shape

        if axis == "rows":
            df_new = df_new.dropna(axis=0, subset=subset).reset_index(drop=True)
            dropped = before_shape[0] - len(df_new)
            impact = f"Dropped {dropped} row(s) containing missing values."
        else:
            # axis == 'columns'
            if thresh is not None:
                # thresh is min non-null ratio
                min_count = int(len(df_new) * thresh)
                df_new = df_new.dropna(axis=1, thresh=min_count)
            else:
                target = subset or list(df_new.columns)
                cols_to_drop = [c for c in target if df_new[c].isna().any()]
                df_new = df_new.drop(columns=cols_to_drop)
            dropped = before_shape[1] - len(df_new.columns)
            impact = f"Dropped {dropped} column(s) containing missing values."

        return df_new, {
            "operation": "drop_missing",
            "axis": axis,
            "shape_before": before_shape,
            "shape_after": df_new.shape,
            "dropped_count": dropped,
            "impact": impact
        }

    @staticmethod
    def convert_column_type(df: pd.DataFrame, column: str, target_type: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Safely convert column type with error guards."""
        df_new = df.copy()
        if column not in df_new.columns:
            return df_new, {"operation": "convert_column_type", "status": "failed", "reason": "Column not found"}

        before_dtype = str(df_new[column].dtype)
        before_nulls = int(df_new[column].isna().sum())

        try:
            if target_type == "numeric":
                # Strip common formatting like $, commas
                if df_new[column].dtype == object:
                    clean_s = df_new[column].astype(str).str.replace(r'[\$,]', '', regex=True)
                else:
                    clean_s = df_new[column]
                converted = pd.to_numeric(clean_s, errors="coerce")
                after_nulls = int(converted.isna().sum())
                # If conversion created unexpected nulls on > 30% of data, mark safety warning
                if (after_nulls - before_nulls) > (0.30 * len(df_new)):
                    return df, {
                        "operation": "convert_column_type",
                        "status": "rejected_unsafe",
                        "reason": f"Type conversion would destroy {after_nulls - before_nulls} values. Rollback applied."
                    }
                df_new[column] = converted

            elif target_type == "datetime":
                df_new[column] = pd.to_datetime(df_new[column], errors="coerce")

            elif target_type == "string":
                df_new[column] = df_new[column].astype(str)

            elif target_type == "category":
                df_new[column] = df_new[column].astype("category")

            after_dtype = str(df_new[column].dtype)
            return df_new, {
                "operation": "convert_column_type",
                "column": column,
                "from_dtype": before_dtype,
                "to_dtype": after_dtype,
                "impact": f"Converted '{column}' from {before_dtype} to {after_dtype}."
            }

        except Exception as e:
            return df, {
                "operation": "convert_column_type",
                "status": "failed",
                "reason": str(e)
            }

    @staticmethod
    def remove_outliers_iqr(df: pd.DataFrame, column: str, factor: float = 1.5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Remove statistical outliers based on IQR with documented thresholds."""
        df_new = df.copy()
        if column not in df_new.columns or not pd.api.types.is_numeric_dtype(df_new[column]):
            return df_new, {"operation": "remove_outliers_iqr", "status": "failed", "reason": "Column is not numeric"}

        s = df_new[column].dropna()
        if len(s) == 0:
            return df_new, {"operation": "remove_outliers_iqr", "status": "skipped", "reason": "No numeric data"}

        q25 = float(s.quantile(0.25))
        q75 = float(s.quantile(0.75))
        iqr = q75 - q25
        lower_bound = q25 - factor * iqr
        upper_bound = q75 + factor * iqr

        mask = (df_new[column] < lower_bound) | (df_new[column] > upper_bound)
        outlier_count = int(mask.sum())

        before_len = len(df_new)
        # Apply filter: keep non-outliers (and keep nulls for separate imputation)
        df_new = df_new[~mask].reset_index(drop=True)
        after_len = len(df_new)

        return df_new, {
            "operation": "remove_outliers_iqr",
            "column": column,
            "bounds": (round(lower_bound, 2), round(upper_bound, 2)),
            "outliers_removed": outlier_count,
            "rows_before": before_len,
            "rows_after": after_len,
            "impact": f"Removed {outlier_count} outlier row(s) in '{column}' outside [{lower_bound:.2f}, {upper_bound:.2f}]."
        }

    @staticmethod
    def scale_features(df: pd.DataFrame, columns: List[str], method: str = "minmax") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Scale numerical features using Min-Max [0, 1] or Z-Score (standard) scaling."""
        df_new = df.copy()
        scaled_cols = []
        for col in columns:
            if col in df_new.columns and pd.api.types.is_numeric_dtype(df_new[col]):
                s = df_new[col].dropna()
                if len(s) > 1:
                    if method == "minmax":
                        min_v = s.min()
                        max_v = s.max()
                        if max_v > min_v:
                            df_new[f"{col}_scaled"] = (df_new[col] - min_v) / (max_v - min_v)
                            scaled_cols.append(f"{col}_scaled")
                    elif method == "standard":
                        mean_v = s.mean()
                        std_v = s.std()
                        if std_v > 0:
                            df_new[f"{col}_standardized"] = (df_new[col] - mean_v) / std_v
                            scaled_cols.append(f"{col}_standardized")

        return df_new, {
            "operation": "scale_features",
            "method": method,
            "created_columns": scaled_cols,
            "impact": f"Generated {len(scaled_cols)} scaled feature column(s) using {method} scaling."
        }

    @staticmethod
    def log_transform(df: pd.DataFrame, column: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply log1p transformation to strictly non-negative column."""
        df_new = df.copy()
        if column not in df_new.columns or not pd.api.types.is_numeric_dtype(df_new[column]):
            return df_new, {"operation": "log_transform", "status": "failed", "reason": "Column not numeric"}

        s = df_new[column].dropna()
        if (s < 0).any():
            return df, {
                "operation": "log_transform",
                "status": "rejected_unsafe",
                "reason": "Log transform requires non-negative values (x >= 0). Dataset contains negative values."
            }

        new_col_name = f"{column}_log"
        df_new[new_col_name] = np.log1p(df_new[column])
        return df_new, {
            "operation": "log_transform",
            "column": column,
            "new_column": new_col_name,
            "impact": f"Created log-transformed column '{new_col_name}' using log1p."
        }

    @staticmethod
    def drop_columns(df: pd.DataFrame, columns: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Drop selected columns."""
        df_new = df.copy()
        existing = [c for c in columns if c in df_new.columns]
        df_new = df_new.drop(columns=existing)
        return df_new, {
            "operation": "drop_columns",
            "dropped_columns": existing,
            "columns_before": len(df.columns),
            "columns_after": len(df_new.columns),
            "impact": f"Dropped column(s): {', '.join(existing)}."
        }

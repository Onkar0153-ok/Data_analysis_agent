"""Automated Data Profiling Engine for DataPilot AI."""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class SemanticType:
    NUMERIC_CONTINUOUS = "numeric_continuous"
    NUMERIC_DISCRETE = "numeric_discrete"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    IDENTIFIER = "identifier"
    FREE_TEXT = "free_text"
    UNKNOWN = "unknown"

class DataProfiler:
    """Performs deep profiling and issue perception on a pandas DataFrame."""

    @staticmethod
    def profile_dataset(df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive profile and detect data quality issues."""
        if df is None or df.empty:
            return {
                "row_count": 0,
                "col_count": 0,
                "missing_cells": 0,
                "missing_rate": 0.0,
                "duplicate_rows": 0,
                "duplicate_rate": 0.0,
                "columns": {},
                "semantic_counts": {},
                "correlations": {},
                "issues": [],
                "warnings": ["Dataset is empty."],
            }

        n_rows, n_cols = df.shape
        total_cells = n_rows * n_cols
        total_missing = int(df.isna().sum().sum())
        missing_rate = (total_missing / total_cells) if total_cells > 0 else 0.0

        duplicate_rows = int(df.duplicated().sum())
        duplicate_rate = (duplicate_rows / n_rows) if n_rows > 0 else 0.0

        columns_profile: Dict[str, Any] = {}
        issues: List[Dict[str, Any]] = []
        semantic_counts: Dict[str, int] = {}

        # If duplicate rows exist, log as dataset issue
        if duplicate_rows > 0:
            issues.append({
                "issue_id": "ISSUE_DUP_ROWS",
                "type": "duplicate_rows",
                "severity": "HIGH" if duplicate_rate > 0.05 else "MEDIUM",
                "target_columns": ["ALL"],
                "description": f"Dataset contains {duplicate_rows} exact duplicate row(s) ({duplicate_rate:.1%}).",
                "count": duplicate_rows,
                "rate": duplicate_rate,
                "suggested_action": "remove_duplicate_rows"
            })

        for col in df.columns:
            col_prof = DataProfiler._profile_column(df[col], col, n_rows)
            columns_profile[col] = col_prof
            
            stype = col_prof["semantic_type"]
            semantic_counts[stype] = semantic_counts.get(stype, 0) + 1

            # Accumulate issues detected in this column
            if col_prof.get("issues"):
                issues.extend(col_prof["issues"])

        # Correlation matrix for continuous & discrete numeric columns (excluding identifiers)
        valid_numeric_cols = [
            c for c, p in columns_profile.items()
            if p["semantic_type"] in [SemanticType.NUMERIC_CONTINUOUS, SemanticType.NUMERIC_DISCRETE]
            and p["unique_count"] > 1
        ]
        
        corr_dict = {}
        if len(valid_numeric_cols) >= 2:
            try:
                corr_matrix = df[valid_numeric_cols].corr().round(3)
                corr_dict = corr_matrix.to_dict()
            except Exception as e:
                logger.warning("Could not calculate correlation: %s", e)

        return {
            "row_count": n_rows,
            "col_count": n_cols,
            "total_cells": total_cells,
            "missing_cells": total_missing,
            "missing_rate": round(missing_rate, 4),
            "duplicate_rows": duplicate_rows,
            "duplicate_rate": round(duplicate_rate, 4),
            "columns": columns_profile,
            "semantic_counts": semantic_counts,
            "correlations": corr_dict,
            "issues": issues,
            "valid_numeric_cols": valid_numeric_cols,
        }

    @staticmethod
    def _profile_column(series: pd.Series, col_name: str, total_rows: int) -> Dict[str, Any]:
        """Profile a single column and identify its semantic type and issues."""
        null_count = int(series.isna().sum())
        non_null_count = total_rows - null_count
        null_rate = (null_count / total_rows) if total_rows > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))
        raw_dtype = str(series.dtype)

        col_issues: List[Dict[str, Any]] = []

        # 1. Missing values issue
        if null_count > 0:
            col_issues.append({
                "issue_id": f"ISSUE_MISSING_{col_name}",
                "type": "missing_values",
                "severity": "HIGH" if null_rate > 0.25 else "MEDIUM",
                "target_columns": [col_name],
                "description": f"Column '{col_name}' has {null_count} missing value(s) ({null_rate:.1%}).",
                "count": null_count,
                "rate": round(null_rate, 4),
                "suggested_action": "impute_or_drop"
            })

        # 2. Constant column issue
        if unique_count <= 1 and non_null_count > 0:
            col_issues.append({
                "issue_id": f"ISSUE_CONSTANT_{col_name}",
                "type": "constant_column",
                "severity": "LOW",
                "target_columns": [col_name],
                "description": f"Column '{col_name}' has only {unique_count} distinct non-null value.",
                "count": unique_count,
                "suggested_action": "drop_constant_column"
            })

        # 3. Infer Semantic Type
        semantic_type = DataProfiler._infer_semantic_type(series, col_name, total_rows, unique_count)

        # 4. Statistical measurements
        stats: Dict[str, Any] = {}
        outlier_info: Dict[str, Any] = {"count": 0, "indices": []}

        # Check for text issues if object/string
        inconsistent_categories: List[str] = []
        whitespace_issues: int = 0
        convertible_to_numeric: bool = False

        if series.dtype == object or pd.api.types.is_string_dtype(series):
            # Check for leading/trailing whitespace
            clean_s = series.dropna().astype(str)
            whitespace_count = int((clean_s != clean_s.str.strip()).sum())
            if whitespace_count > 0:
                whitespace_issues = whitespace_count
                col_issues.append({
                    "issue_id": f"ISSUE_WHITESPACE_{col_name}",
                    "type": "whitespace",
                    "severity": "LOW",
                    "target_columns": [col_name],
                    "description": f"Column '{col_name}' has {whitespace_count} value(s) with leading/trailing whitespace.",
                    "count": whitespace_count,
                    "suggested_action": "trim_whitespace"
                })

            # Check for case inconsistency in categories (e.g., 'North' and 'north')
            if semantic_type in [SemanticType.CATEGORICAL] and unique_count < 100:
                unique_vals = clean_s.str.strip().unique()
                lower_map = {}
                for v in unique_vals:
                    low = v.lower()
                    lower_map.setdefault(low, []).append(v)
                inconsistent_groups = [vals for vals in lower_map.values() if len(vals) > 1]
                if inconsistent_groups:
                    inconsistent_categories = [item for sub in inconsistent_groups for item in sub]
                    col_issues.append({
                        "issue_id": f"ISSUE_CASE_INCONSISTENCY_{col_name}",
                        "type": "inconsistent_categories",
                        "severity": "MEDIUM",
                        "target_columns": [col_name],
                        "description": f"Column '{col_name}' has case-inconsistent categories: {inconsistent_groups[:3]}",
                        "groups": inconsistent_groups,
                        "suggested_action": "standardize_case"
                    })

            # Check if object column is secretly numeric (e.g., currency symbols or commas)
            if semantic_type not in [SemanticType.DATETIME, SemanticType.IDENTIFIER]:
                num_converted = pd.to_numeric(clean_s.str.replace(r'[\$,]', '', regex=True), errors="coerce")
                valid_num_rate = (num_converted.notna().sum() / len(clean_s)) if len(clean_s) > 0 else 0
                if valid_num_rate > 0.85 and semantic_type != SemanticType.NUMERIC_CONTINUOUS:
                    convertible_to_numeric = True
                    col_issues.append({
                        "issue_id": f"ISSUE_SUSPICIOUS_TYPE_{col_name}",
                        "type": "suspicious_data_type",
                        "severity": "MEDIUM",
                        "target_columns": [col_name],
                        "description": f"Column '{col_name}' is stored as text but {valid_num_rate:.1%} of values are numeric.",
                        "suggested_action": "convert_to_numeric"
                    })

        # Numeric stats and outlier detection (strictly non-boolean)
        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series) and semantic_type not in [SemanticType.IDENTIFIER, SemanticType.BOOLEAN]:
            s_clean = series.dropna()
            if len(s_clean) > 0:
                q25 = float(s_clean.quantile(0.25))
                q50 = float(s_clean.quantile(0.50))
                q75 = float(s_clean.quantile(0.75))
                iqr = q75 - q25
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
                
                outliers = s_clean[(s_clean < lower_bound) | (s_clean > upper_bound)]
                outlier_count = len(outliers)
                outlier_info = {
                    "count": outlier_count,
                    "lower_bound": round(lower_bound, 4),
                    "upper_bound": round(upper_bound, 4),
                    "outlier_rate": round(outlier_count / len(s_clean), 4),
                }

                if outlier_count > 0:
                    col_issues.append({
                        "issue_id": f"ISSUE_OUTLIER_{col_name}",
                        "type": "outliers",
                        "severity": "MEDIUM" if outlier_count / len(s_clean) < 0.05 else "HIGH",
                        "target_columns": [col_name],
                        "description": f"Column '{col_name}' has {outlier_count} statistical outlier(s) (beyond IQR [{lower_bound:.2f}, {upper_bound:.2f}]).",
                        "count": outlier_count,
                        "bounds": (round(lower_bound, 2), round(upper_bound, 2)),
                        "suggested_action": "review_outliers"
                    })

                stats = {
                    "mean": round(float(s_clean.mean()), 4),
                    "std": round(float(s_clean.std()), 4) if len(s_clean) > 1 else 0.0,
                    "min": round(float(s_clean.min()), 4),
                    "q25": round(q25, 4),
                    "median": round(q50, 4),
                    "q75": round(q75, 4),
                    "max": round(float(s_clean.max()), 4),
                    "skewness": round(float(s_clean.skew()), 4) if len(s_clean) > 2 else 0.0,
                }

        # Categorical distribution / top values
        top_values = {}
        if non_null_count > 0:
            top_counts = series.value_counts(dropna=True).head(5)
            top_values = {str(k): int(v) for k, v in top_counts.items()}

        return {
            "name": col_name,
            "raw_dtype": raw_dtype,
            "semantic_type": semantic_type,
            "total_rows": total_rows,
            "non_null_count": non_null_count,
            "null_count": null_count,
            "null_rate": round(null_rate, 4),
            "unique_count": unique_count,
            "uniqueness_ratio": round(unique_count / total_rows, 4) if total_rows > 0 else 0.0,
            "stats": stats,
            "outlier_info": outlier_info,
            "top_values": top_values,
            "whitespace_issues": whitespace_issues,
            "inconsistent_categories": inconsistent_categories,
            "convertible_to_numeric": convertible_to_numeric,
            "issues": col_issues,
        }

    @staticmethod
    def _infer_semantic_type(series: pd.Series, col_name: str, total_rows: int, unique_count: int) -> str:
        """Infer semantic type accurately distinguishing identifiers, dates, categories, and measures."""
        col_lower = col_name.lower()
        non_null = series.dropna()

        # 1. Identifier detection
        # Column names like id, code, key, uuid, number, no, order_id, customer_id
        is_id_name = any(col_lower.endswith(sfx) for sfx in ["_id", "id", "_code", "key", "_no", "uuid", "guid"]) or col_lower in ["id", "code", "index"]
        if is_id_name:
            # If high uniqueness or formatted with letters and numbers (like ORD-1001)
            if unique_count / total_rows > 0.85 or (len(non_null) > 0 and non_null.astype(str).str.contains(r'^[A-Za-z]+[-_0-9]').any()):
                return SemanticType.IDENTIFIER

        # 2. Boolean detection
        if pd.api.types.is_bool_dtype(series):
            return SemanticType.BOOLEAN
        if unique_count == 2 and set(non_null.astype(str).str.lower().unique()).issubset({"true", "false", "0", "1", "yes", "no", "y", "n"}):
            return SemanticType.BOOLEAN

        # 3. Datetime detection
        if pd.api.types.is_datetime64_any_dtype(series):
            return SemanticType.DATETIME
        if series.dtype == object or pd.api.types.is_string_dtype(series):
            # Check date-like names or attempt parsing a small sample
            if any(date_word in col_lower for date_word in ["date", "time", "created", "timestamp", "year", "month"]):
                sample = non_null.head(10).astype(str)
                try:
                    pd.to_datetime(sample, errors="raise")
                    return SemanticType.DATETIME
                except Exception:
                    pass

        # 4. Numeric continuous vs discrete
        if pd.api.types.is_numeric_dtype(series):
            if unique_count / total_rows > 0.95 and is_id_name:
                return SemanticType.IDENTIFIER
            if pd.api.types.is_float_dtype(series):
                return SemanticType.NUMERIC_CONTINUOUS
            if pd.api.types.is_integer_dtype(series):
                return SemanticType.NUMERIC_DISCRETE if unique_count < 25 else SemanticType.NUMERIC_CONTINUOUS

        # 5. Categorical vs Free Text
        if series.dtype == object or pd.api.types.is_string_dtype(series):
            if unique_count <= 50 or (total_rows > 0 and (unique_count / total_rows) < 0.20):
                return SemanticType.CATEGORICAL
            # If average length is long or high cardinality
            avg_len = non_null.astype(str).str.len().mean() if len(non_null) > 0 else 0
            if avg_len > 40:
                return SemanticType.FREE_TEXT
            return SemanticType.CATEGORICAL

        return SemanticType.UNKNOWN

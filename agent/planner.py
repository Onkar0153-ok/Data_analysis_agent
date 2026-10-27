"""Autonomous Planning Engine for DataPilot AI."""

import logging
from typing import Dict, Any, List
from agent.models import PlannedAction, ActionRisk, ActionStatus
from agent.policies import AgentPolicy

logger = logging.getLogger(__name__)

class AgentPlanner:
    """Perceives dataset profile and formulates an ordered, risk-classified cleaning plan."""

    @staticmethod
    def create_cleaning_plan(profile: Dict[str, Any], auto_execute_safe: bool = True) -> List[PlannedAction]:
        """Construct a dependency-ordered plan of actions to resolve detected issues."""
        actions: List[PlannedAction] = []
        issues = profile.get("issues", [])
        columns_meta = profile.get("columns", {})

        action_idx = 1

        # Priority 1: Trim Whitespace
        whitespace_cols = [
            col for col, meta in columns_meta.items()
            if meta.get("whitespace_issues", 0) > 0
        ]
        if whitespace_cols:
            risk = AgentPolicy.get_risk_level("trim_whitespace", {})
            actions.append(PlannedAction(
                action_id=f"ACT_{action_idx:02d}_TRIM_WHITESPACE",
                issue_id="ISSUE_WHITESPACE",
                target_columns=whitespace_cols,
                operation_name="trim_whitespace",
                parameters={"columns": whitespace_cols},
                reason=f"Remove unnecessary whitespace in {len(whitespace_cols)} column(s) to standardize text records.",
                risk_level=risk,
                needs_approval=AgentPolicy.requires_approval(risk, auto_execute_safe)
            ))
            action_idx += 1

        # Priority 2: Standardize Inconsistent Categories / Case
        for col, meta in columns_meta.items():
            inconsistent = meta.get("inconsistent_categories", [])
            if inconsistent:
                risk = AgentPolicy.get_risk_level("standardize_equivalent_categories", {})
                actions.append(PlannedAction(
                    action_id=f"ACT_{action_idx:02d}_STANDARDIZE_{col.upper()}",
                    issue_id=f"ISSUE_CASE_INCONSISTENCY_{col}",
                    target_columns=[col],
                    operation_name="standardize_equivalent_categories",
                    parameters={"column": col},
                    reason=f"Unify case-variant labels in column '{col}' to prevent fragmented category grouping.",
                    risk_level=risk,
                    needs_approval=AgentPolicy.requires_approval(risk, auto_execute_safe)
                ))
                action_idx += 1

        # Priority 3: Remove Exact Duplicate Rows
        dup_rows = profile.get("duplicate_rows", 0)
        if dup_rows > 0:
            risk = AgentPolicy.get_risk_level("remove_duplicate_rows", {})
            actions.append(PlannedAction(
                action_id=f"ACT_{action_idx:02d}_REMOVE_DUPLICATES",
                issue_id="ISSUE_DUP_ROWS",
                target_columns=["ALL"],
                operation_name="remove_duplicate_rows",
                parameters={},
                reason=f"Eliminate {dup_rows} exact redundant row(s) to prevent statistical double-counting.",
                risk_level=risk,
                needs_approval=AgentPolicy.requires_approval(risk, auto_execute_safe)
            ))
            action_idx += 1

        # Priority 4: Suspicious Data Type Conversion
        for col, meta in columns_meta.items():
            if meta.get("convertible_to_numeric"):
                risk = AgentPolicy.get_risk_level("convert_column_type", {})
                actions.append(PlannedAction(
                    action_id=f"ACT_{action_idx:02d}_CONVERT_NUMERIC_{col.upper()}",
                    issue_id=f"ISSUE_SUSPICIOUS_TYPE_{col}",
                    target_columns=[col],
                    operation_name="convert_column_type",
                    parameters={"column": col, "target_type": "numeric"},
                    reason=f"Convert '{col}' to numeric to enable statistical computation and aggregations.",
                    risk_level=risk,
                    needs_approval=AgentPolicy.requires_approval(risk, auto_execute_safe)
                ))
                action_idx += 1

        # Priority 5: Impute Missing Values
        for col, meta in columns_meta.items():
            null_count = meta.get("null_count", 0)
            if null_count > 0:
                stype = meta.get("semantic_type")
                if stype in ["numeric_continuous", "numeric_discrete"]:
                    op_name = "impute_missing_numeric"
                    # Default strategy: median is robust to outliers
                    strategy = "median"
                    params = {"column": col, "strategy": strategy}
                    reason = f"Impute {null_count} missing numerical entries in '{col}' using robust median value."
                else:
                    op_name = "impute_missing_categorical"
                    strategy = "mode"
                    params = {"column": col, "strategy": strategy}
                    reason = f"Impute {null_count} missing categorical entries in '{col}' using most frequent category (mode)."

                risk = AgentPolicy.get_risk_level(op_name, params)
                actions.append(PlannedAction(
                    action_id=f"ACT_{action_idx:02d}_IMPUTE_{col.upper()}",
                    issue_id=f"ISSUE_MISSING_{col}",
                    target_columns=[col],
                    operation_name=op_name,
                    parameters=params,
                    reason=reason,
                    risk_level=risk,
                    needs_approval=AgentPolicy.requires_approval(risk, auto_execute_safe)
                ))
                action_idx += 1

        # Priority 6: Statistical Outliers (High Risk - Requires explicit user approval)
        for col, meta in columns_meta.items():
            outlier_info = meta.get("outlier_info", {})
            outlier_count = outlier_info.get("count", 0)
            if outlier_count > 0:
                risk = AgentPolicy.get_risk_level("remove_outliers_iqr", {})
                actions.append(PlannedAction(
                    action_id=f"ACT_{action_idx:02d}_FILTER_OUTLIERS_{col.upper()}",
                    issue_id=f"ISSUE_OUTLIER_{col}",
                    target_columns=[col],
                    operation_name="remove_outliers_iqr",
                    parameters={"column": col, "factor": 1.5},
                    reason=f"Filter {outlier_count} statistical outlier row(s) in '{col}' outside 1.5*IQR bounds.",
                    risk_level=risk,
                    needs_approval=True  # Always requires approval because it removes observations
                ))
                action_idx += 1

        return actions

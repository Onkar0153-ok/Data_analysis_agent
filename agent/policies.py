"""Risk classification policies and execution guidelines for DataPilot AI."""

from typing import Dict, Any
from agent.models import ActionRisk

class AgentPolicy:
    """Manages risk classifications and auto-execution eligibility."""

    # Explicit risk mappings for operations
    OPERATION_RISK_MAP = {
        "trim_whitespace": ActionRisk.SAFE,
        "standardize_equivalent_categories": ActionRisk.SAFE,
        "remove_duplicate_rows": ActionRisk.SAFE,
        "normalize_text_case": ActionRisk.SAFE,
        "impute_missing_numeric": ActionRisk.REVIEW_RECOMMENDED,
        "impute_missing_categorical": ActionRisk.REVIEW_RECOMMENDED,
        "convert_column_type": ActionRisk.REVIEW_RECOMMENDED,
        "scale_features": ActionRisk.REVIEW_RECOMMENDED,
        "log_transform": ActionRisk.REVIEW_RECOMMENDED,
        "remove_outliers_iqr": ActionRisk.HIGH_RISK,
        "drop_columns": ActionRisk.HIGH_RISK,
        "drop_missing": ActionRisk.HIGH_RISK,
    }

    @staticmethod
    def get_risk_level(operation_name: str, params: Dict[str, Any]) -> str:
        """Determine risk level of an operation based on type and arguments."""
        # Special check: dropping rows with missing values is higher risk if dropping > 10%
        base_risk = AgentPolicy.OPERATION_RISK_MAP.get(operation_name, ActionRisk.REVIEW_RECOMMENDED)
        return base_risk

    @staticmethod
    def requires_approval(risk_level: str, auto_execute_safe: bool = True) -> bool:
        """Check if action requires user confirmation."""
        if risk_level == ActionRisk.SAFE:
            return not auto_execute_safe
        # REVIEW_RECOMMENDED and HIGH_RISK always require approval in default policy
        return True

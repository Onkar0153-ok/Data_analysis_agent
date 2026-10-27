"""Validation helpers for schemas, uploads, and operation manifests."""

from typing import Dict, Any, List, Tuple
import pandas as pd

class SchemaValidator:
    """Validates dataset compatibility and operation manifests before replay."""

    @staticmethod
    def validate_schema_match(df: pd.DataFrame, expected_schema: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Verify whether a dataset conforms to the expected columns and types."""
        errors = []
        actual_cols = set(df.columns)
        expected_cols = set(expected_schema.keys())

        missing = expected_cols - actual_cols
        if missing:
            errors.append(f"Missing required column(s): {', '.join(sorted(missing))}")

        # Check types for present columns
        for col, expected_dtype in expected_schema.items():
            if col in df.columns:
                actual_dtype = str(df[col].dtype)
                # Allow general numeric compatibility
                if "int" in expected_dtype and "int" in actual_dtype:
                    continue
                if "float" in expected_dtype and ("float" in actual_dtype or "int" in actual_dtype):
                    continue
                if expected_dtype != actual_dtype:
                    errors.append(f"Column '{col}' expected type '{expected_dtype}', found '{actual_dtype}'")

        return len(errors) == 0, errors

    @staticmethod
    def validate_manifest_structure(manifest: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Ensure manifest contains valid ordered operations."""
        if not isinstance(manifest, list):
            return False, "Manifest must be a list of operation items."

        for idx, item in enumerate(manifest):
            if not isinstance(item, dict):
                return False, f"Manifest item #{idx} is not a valid dictionary."
            if "operation_name" not in item:
                return False, f"Manifest item #{idx} is missing 'operation_name'."
            if "parameters" not in item:
                return False, f"Manifest item #{idx} is missing 'parameters'."

        return True, "Manifest structure verified."

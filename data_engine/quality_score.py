"""Explainable Heuristic Data Quality Scoring Engine for DataPilot AI."""

from typing import Dict, Any
from config.settings import QUALITY_WEIGHTS

class QualityScoreCalculator:
    """Calculates an explainable data quality score between 0 and 100 based on measurable indicators."""

    @staticmethod
    def calculate_score(profile: Dict[str, Any]) -> Dict[str, Any]:
        """Compute holistic heuristic quality score and individual dimension breakdowns.
        
        Indicators:
        1. Completeness (35 pts): Ratio of non-missing cells.
        2. Uniqueness (25 pts): Absence of exact duplicate records.
        3. Type Integrity (20 pts): Absence of constant columns, suspicious mixed types.
        4. Consistency (20 pts): Absence of whitespace flaws, case inconsistency, and extreme outliers.
        """
        row_count = profile.get("row_count", 0)
        col_count = profile.get("col_count", 0)

        if row_count == 0 or col_count == 0:
            return {
                "overall_score": 0.0,
                "grade": "F",
                "breakdown": {
                    "completeness": {"score": 0.0, "max": QUALITY_WEIGHTS["completeness"], "percentage": 0.0, "notes": "No data"},
                    "uniqueness": {"score": 0.0, "max": QUALITY_WEIGHTS["uniqueness"], "percentage": 0.0, "notes": "No data"},
                    "type_integrity": {"score": 0.0, "max": QUALITY_WEIGHTS["type_integrity"], "percentage": 0.0, "notes": "No data"},
                    "consistency": {"score": 0.0, "max": QUALITY_WEIGHTS["consistency"], "percentage": 0.0, "notes": "No data"},
                },
                "explanation": "Dataset is empty."
            }

        # 1. Completeness (35 points)
        missing_rate = profile.get("missing_rate", 0.0)
        completeness_ratio = max(0.0, 1.0 - missing_rate)
        completeness_score = round(completeness_ratio * QUALITY_WEIGHTS["completeness"], 1)

        # 2. Uniqueness (25 points)
        duplicate_rate = profile.get("duplicate_rate", 0.0)
        # Heavy penalty for duplicates: if 10% duplicates, uniqueness drops significantly
        uniqueness_ratio = max(0.0, 1.0 - (duplicate_rate * 2.0))
        uniqueness_score = round(uniqueness_ratio * QUALITY_WEIGHTS["uniqueness"], 1)

        # 3. Type Integrity (20 points)
        columns = profile.get("columns", {})
        type_penalties = 0.0
        for col_name, cinfo in columns.items():
            if cinfo.get("convertible_to_numeric"):
                type_penalties += 0.3  # Stored as text when numeric
            if cinfo.get("unique_count", 0) <= 1 and cinfo.get("non_null_count", 0) > 0:
                type_penalties += 0.2  # Constant uninformative column
        
        type_ratio = max(0.0, 1.0 - min(1.0, type_penalties / max(1, col_count)))
        type_integrity_score = round(type_ratio * QUALITY_WEIGHTS["type_integrity"], 1)

        # 4. Consistency (20 points)
        consistency_penalties = 0.0
        for col_name, cinfo in columns.items():
            if cinfo.get("whitespace_issues", 0) > 0:
                consistency_penalties += 0.2
            if len(cinfo.get("inconsistent_categories", [])) > 0:
                consistency_penalties += 0.25
            outliers = cinfo.get("outlier_info", {}).get("count", 0)
            if outliers > 0:
                outlier_rate = cinfo.get("outlier_info", {}).get("outlier_rate", 0.0)
                if outlier_rate > 0.10:
                    consistency_penalties += 0.3
                else:
                    consistency_penalties += 0.15

        consistency_ratio = max(0.0, 1.0 - min(1.0, consistency_penalties / max(1, col_count)))
        consistency_score = round(consistency_ratio * QUALITY_WEIGHTS["consistency"], 1)

        # Overall Score
        total_score = round(completeness_score + uniqueness_score + type_integrity_score + consistency_score, 1)
        total_score = max(0.0, min(100.0, total_score))

        # Assign letter grade
        if total_score >= 90:
            grade = "A"
        elif total_score >= 80:
            grade = "B"
        elif total_score >= 70:
            grade = "C"
        elif total_score >= 60:
            grade = "D"
        else:
            grade = "F"

        breakdown = {
            "completeness": {
                "score": completeness_score,
                "max": QUALITY_WEIGHTS["completeness"],
                "percentage": round((completeness_score / QUALITY_WEIGHTS["completeness"]) * 100, 1),
                "notes": f"Missing cell rate: {missing_rate:.1%}"
            },
            "uniqueness": {
                "score": uniqueness_score,
                "max": QUALITY_WEIGHTS["uniqueness"],
                "percentage": round((uniqueness_score / QUALITY_WEIGHTS["uniqueness"]) * 100, 1),
                "notes": f"Duplicate row rate: {duplicate_rate:.1%}"
            },
            "type_integrity": {
                "score": type_integrity_score,
                "max": QUALITY_WEIGHTS["type_integrity"],
                "percentage": round((type_integrity_score / QUALITY_WEIGHTS["type_integrity"]) * 100, 1),
                "notes": f"Evaluated across {col_count} columns"
            },
            "consistency": {
                "score": consistency_score,
                "max": QUALITY_WEIGHTS["consistency"],
                "percentage": round((consistency_score / QUALITY_WEIGHTS["consistency"]) * 100, 1),
                "notes": "Whitespace, casing, and statistical bounds"
            }
        }

        explanation = (
            f"Overall score {total_score}/100 (Grade {grade}). "
            f"Completeness is {breakdown['completeness']['percentage']}%, "
            f"Uniqueness is {breakdown['uniqueness']['percentage']}%, "
            f"Type Integrity is {breakdown['type_integrity']['percentage']}%, and "
            f"Consistency is {breakdown['consistency']['percentage']}%."
        )

        return {
            "overall_score": total_score,
            "grade": grade,
            "breakdown": breakdown,
            "explanation": explanation
        }

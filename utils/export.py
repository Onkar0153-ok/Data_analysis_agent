"""Exporting and Reporting utilities for DataPilot AI."""

import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
import pandas as pd

from data_engine.preprocessing import PreprocessingEngine
from utils.validation import SchemaValidator

class ReportExporter:
    """Generates rich standalone HTML reports and exportable manifests."""

    @staticmethod
    def generate_html_report(
        metadata: Dict[str, Any],
        profile_before: Dict[str, Any],
        profile_after: Dict[str, Any],
        score_before: Dict[str, Any],
        score_after: Dict[str, Any],
        operations_manifest: List[Dict[str, Any]],
        activity_logs: List[Dict[str, Any]],
        comparison_metrics: Dict[str, Any]
    ) -> str:
        """Construct a polished, standalone HTML audit and analysis report."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = metadata.get("filename", "Dataset")

        # Operations rows
        op_rows = ""
        for op in operations_manifest:
            status_color = "#10B981" if op.get("execution_status") == "PASSED" else "#EF4444"
            op_rows += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #273449;"><code>{op.get('operation_id')}</code></td>
                <td style="padding: 10px; border-bottom: 1px solid #273449;"><strong>{op.get('operation_name')}</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #273449;">{op.get('target_columns')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #273449;"><span style="color: {status_color}; font-weight: bold;">{op.get('execution_status')}</span></td>
                <td style="padding: 10px; border-bottom: 1px solid #273449;"><pre style="margin:0; font-size:11px;">{json.dumps(op.get('parameters', {}))}</pre></td>
            </tr>
            """

        if not op_rows:
            op_rows = "<tr><td colspan='5' style='padding: 12px; text-align: center; color: #94A3B8;'>No automated cleaning operations recorded.</td></tr>"

        # Comparison metrics
        score_diff = score_after.get("overall_score", 0) - score_before.get("overall_score", 0)
        score_color = "#10B981" if score_diff >= 0 else "#EF4444"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DataPilot AI Analysis Report - {filename}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0B1220;
            color: #F8FAFC;
            margin: 0;
            padding: 40px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #141F32;
            border: 1px solid #273449;
            border-radius: 12px;
            padding: 30px;
        }}
        .header {{
            border-bottom: 1px solid #273449;
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}
        h1, h2, h3 {{
            color: #22D3EE;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #1E293B;
            border: 1px solid #273449;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }}
        .metric-val {{
            font-size: 24px;
            font-weight: bold;
            color: #F8FAFC;
            margin-top: 5px;
        }}
        .metric-label {{
            font-size: 12px;
            color: #94A3B8;
            text-transform: uppercase;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background: #1E293B;
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background: #111827;
            color: #22D3EE;
            text-align: left;
            padding: 12px;
            font-size: 13px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #273449;
            font-size: 12px;
            color: #94A3B8;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>DataPilot AI — Executive Analysis & Audit Report</h1>
            <p style="color: #94A3B8;">Dataset: <strong>{filename}</strong> | Generated: <strong>{now_str}</strong></p>
        </div>

        <h2>1. Data Quality & Preprocessing Overview</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Initial Quality Score</div>
                <div class="metric-val">{score_before.get('overall_score', 0)} / 100 ({score_before.get('grade', 'N/A')})</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Cleaned Quality Score</div>
                <div class="metric-val" style="color: {score_color};">{score_after.get('overall_score', 0)} / 100 ({score_after.get('grade', 'N/A')})</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Row Count Change</div>
                <div class="metric-val">{comparison_metrics.get('rows_before', 0)} &rarr; {comparison_metrics.get('rows_after', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Missing Cells</div>
                <div class="metric-val">{comparison_metrics.get('missing_before', 0)} &rarr; {comparison_metrics.get('missing_after', 0)}</div>
            </div>
        </div>

        <h2>2. Executed Cleaning & Transformation Operations</h2>
        <table>
            <thead>
                <tr>
                    <th>Action ID</th>
                    <th>Operation</th>
                    <th>Target Columns</th>
                    <th>Status</th>
                    <th>Parameters</th>
                </tr>
            </thead>
            <tbody>
                {op_rows}
            </tbody>
        </table>

        <h2>3. Before-and-After Dimension Quality Breakdown</h2>
        <table>
            <thead>
                <tr>
                    <th>Dimension</th>
                    <th>Original Score</th>
                    <th>Cleaned Score</th>
                    <th>Max Weight</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">Completeness</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">{score_before.get('breakdown', {}).get('completeness', {}).get('score', 0)}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">{score_after.get('breakdown', {}).get('completeness', {}).get('score', 0)}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">35 pts</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">{score_after.get('breakdown', {}).get('completeness', {}).get('notes', '')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">Uniqueness</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">{score_before.get('breakdown', {}).get('uniqueness', {}).get('score', 0)}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">{score_after.get('breakdown', {}).get('uniqueness', {}).get('score', 0)}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">25 pts</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">{score_after.get('breakdown', {}).get('uniqueness', {}).get('notes', '')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">Type Integrity</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">{score_before.get('breakdown', {}).get('type_integrity', {}).get('score', 0)}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">{score_after.get('breakdown', {}).get('type_integrity', {}).get('score', 0)}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">20 pts</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">{score_after.get('breakdown', {}).get('type_integrity', {}).get('notes', '')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">Consistency</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">{score_before.get('breakdown', {}).get('consistency', {}).get('score', 0)}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">{score_after.get('breakdown', {}).get('consistency', {}).get('score', 0)}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">20 pts</td>
                    <td style="padding: 10px; border-bottom: 1px solid #273449;">{score_after.get('breakdown', {}).get('consistency', {}).get('notes', '')}</td>
                </tr>
            </tbody>
        </table>

        <h2>4. Audit Summary & Caveats</h2>
        <p style="color: #94A3B8; font-size: 13px; line-height: 1.6;">
            DataPilot AI implements risk-aware preprocessing with automated validation gates and snapshot rollbacks.
            Scores reflect heuristic quality metrics (completeness, uniqueness, types, and consistency).
            A high heuristic score indicates syntactic cleanliness and does not guarantee dataset domain accuracy or statistical representativeness.
        </p>

        <div class="footer">
            Generated autonomously by DataPilot AI &bull; Autonomous Agent for Intelligent Data Analysis
        </div>
    </div>
</body>
</html>"""
        return html_content

    @staticmethod
    def replay_manifest(
        df_target: pd.DataFrame,
        manifest: List[Dict[str, Any]]
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Replay an exported operation manifest against a target dataset with schema validation."""
        valid, msg = SchemaValidator.validate_manifest_structure(manifest)
        if not valid:
            raise ValueError(f"Invalid manifest: {msg}")

        df_working = df_target.copy()
        replay_log = []

        for item in manifest:
            op_name = item.get("operation_name")
            params = item.get("parameters", {})
            try:
                # Dispatch operation
                if op_name == "remove_duplicate_rows":
                    df_working, metrics = PreprocessingEngine.remove_duplicate_rows(df_working, **params)
                elif op_name == "trim_whitespace":
                    df_working, metrics = PreprocessingEngine.trim_whitespace(df_working, **params)
                elif op_name == "normalize_text_case":
                    df_working, metrics = PreprocessingEngine.normalize_text_case(df_working, **params)
                elif op_name == "standardize_equivalent_categories":
                    df_working, metrics = PreprocessingEngine.standardize_equivalent_categories(df_working, **params)
                elif op_name == "impute_missing_numeric":
                    df_working, metrics = PreprocessingEngine.impute_missing_numeric(df_working, **params)
                elif op_name == "impute_missing_categorical":
                    df_working, metrics = PreprocessingEngine.impute_missing_categorical(df_working, **params)
                elif op_name == "convert_column_type":
                    df_working, metrics = PreprocessingEngine.convert_column_type(df_working, **params)
                elif op_name == "remove_outliers_iqr":
                    df_working, metrics = PreprocessingEngine.remove_outliers_iqr(df_working, **params)
                elif op_name == "scale_features":
                    df_working, metrics = PreprocessingEngine.scale_features(df_working, **params)
                elif op_name == "log_transform":
                    df_working, metrics = PreprocessingEngine.log_transform(df_working, **params)
                elif op_name == "drop_columns":
                    df_working, metrics = PreprocessingEngine.drop_columns(df_working, **params)
                else:
                    metrics = {"status": "skipped", "reason": f"Unknown operation: {op_name}"}

                replay_log.append({
                    "operation_name": op_name,
                    "status": "SUCCESS",
                    "metrics": metrics
                })
            except Exception as e:
                replay_log.append({
                    "operation_name": op_name,
                    "status": "FAILED",
                    "error": str(e)
                })

        return df_working, replay_log

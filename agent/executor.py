"""Autonomous Execution and Self-Correction Engine for DataPilot AI."""

import logging
from typing import Dict, Any, Tuple, Optional
import pandas as pd

from agent.models import PlannedAction, ActionStatus, AgentEvent
from agent.validator import AgentValidator
from data_engine.preprocessing import PreprocessingEngine
from storage.db import db_manager

logger = logging.getLogger(__name__)

class AgentExecutor:
    """Executes actions with pre-execution snapshots, validation, and bounded self-correction."""

    @staticmethod
    def execute_action(
        df_current: pd.DataFrame,
        action: PlannedAction,
        session_id: str = "default_session"
    ) -> Tuple[pd.DataFrame, PlannedAction, AgentEvent]:
        """Execute a single planned action with snapshot safeguards and validation."""
        snapshot = df_current.copy()
        action.status = ActionStatus.EXECUTING

        # Record start event
        logger.info("Executing action: %s (%s)", action.action_id, action.operation_name)

        # Attempt execution with adaptation loop (bounded retries)
        while action.retry_count <= action.max_retries:
            try:
                df_candidate, exec_metrics = AgentExecutor._dispatch_operation(snapshot, action)
                action.execution_result = exec_metrics

                # Run validation
                is_valid, val_reason, val_metrics = AgentValidator.validate_operation(
                    snapshot, df_candidate, action, exec_metrics
                )
                action.validation_result = {
                    "is_valid": is_valid,
                    "reason": val_reason,
                    "metrics": val_metrics
                }

                if is_valid:
                    action.status = ActionStatus.PASSED
                    event = AgentEvent.create(
                        event_type="OPERATION_PASSED",
                        action_id=action.action_id,
                        decision_summary=f"Successfully executed '{action.operation_name}': {exec_metrics.get('impact', '')}",
                        status="PASSED",
                        validation_result=val_reason,
                        details={"metrics": exec_metrics}
                    )
                    
                    # Log to database
                    db_manager.log_activity(
                        session_id=session_id,
                        event_type="OPERATION_PASSED",
                        decision_summary=event.decision_summary,
                        action_id=action.action_id,
                        status="PASSED",
                        validation_result=val_reason,
                        details=exec_metrics
                    )
                    db_manager.log_cleaning_operation(
                        session_id=session_id,
                        operation_id=action.action_id,
                        operation_name=action.operation_name,
                        target_columns=",".join(action.target_columns),
                        parameters=action.parameters,
                        execution_status="PASSED",
                        before_metrics={"rows": len(snapshot), "cols": len(snapshot.columns)},
                        after_metrics={"rows": len(df_candidate), "cols": len(df_candidate.columns)}
                    )

                    return df_candidate, action, event

                else:
                    # Validation failed: Rollback
                    logger.warning("Validation failed for %s: %s", action.action_id, val_reason)
                    action.retry_count += 1

                    # Check if an alternative strategy can be adapted
                    adapted = AgentExecutor._attempt_adaptation(action)
                    if adapted and action.retry_count <= action.max_retries:
                        logger.info("Adapting strategy for %s (attempt %d)", action.action_id, action.retry_count)
                        continue
                    else:
                        action.status = ActionStatus.ROLLED_BACK
                        event = AgentEvent.create(
                            event_type="ROLLBACK_TRIGGERED",
                            action_id=action.action_id,
                            decision_summary=f"Validation failed for '{action.operation_name}'. Restored previous valid state: {val_reason}",
                            status="ROLLED_BACK",
                            validation_result=val_reason,
                            details={"failed_metrics": exec_metrics}
                        )
                        db_manager.log_activity(
                            session_id=session_id,
                            event_type="ROLLBACK_TRIGGERED",
                            decision_summary=event.decision_summary,
                            action_id=action.action_id,
                            status="ROLLED_BACK",
                            validation_result=val_reason,
                            details={"error": val_reason}
                        )
                        return snapshot, action, event

            except Exception as e:
                logger.exception("Runtime exception in action %s", action.action_id)
                action.retry_count += 1
                action.status = ActionStatus.FAILED
                event = AgentEvent.create(
                    event_type="OPERATION_FAILED",
                    action_id=action.action_id,
                    decision_summary=f"Exception executing '{action.operation_name}': {str(e)}. Restored snapshot.",
                    status="FAILED",
                    validation_result=str(e)
                )
                db_manager.log_activity(
                    session_id=session_id,
                    event_type="OPERATION_FAILED",
                    decision_summary=event.decision_summary,
                    action_id=action.action_id,
                    status="FAILED",
                    validation_result=str(e)
                )
                return snapshot, action, event

        # Exceeded retries
        action.status = ActionStatus.FAILED
        event = AgentEvent.create(
            event_type="RETRIES_EXCEEDED",
            action_id=action.action_id,
            decision_summary=f"Exceeded maximum retries ({action.max_retries}) for '{action.operation_name}'. Restored previous valid state.",
            status="FAILED"
        )
        return snapshot, action, event

    @staticmethod
    def _dispatch_operation(df: pd.DataFrame, action: PlannedAction) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Dispatch operation to PreprocessingEngine based on action specification."""
        op = action.operation_name
        params = action.parameters

        if op == "remove_duplicate_rows":
            return PreprocessingEngine.remove_duplicate_rows(df, subset=params.get("subset"))

        elif op == "trim_whitespace":
            return PreprocessingEngine.trim_whitespace(df, columns=params.get("columns"))

        elif op == "normalize_text_case":
            return PreprocessingEngine.normalize_text_case(
                df, columns=params.get("columns", []), case_style=params.get("case_style", "title")
            )

        elif op == "standardize_equivalent_categories":
            return PreprocessingEngine.standardize_equivalent_categories(
                df, column=params.get("column", ""), mapping=params.get("mapping")
            )

        elif op == "impute_missing_numeric":
            return PreprocessingEngine.impute_missing_numeric(
                df, column=params.get("column", ""), strategy=params.get("strategy", "median"),
                fill_value=params.get("fill_value")
            )

        elif op == "impute_missing_categorical":
            return PreprocessingEngine.impute_missing_categorical(
                df, column=params.get("column", ""), strategy=params.get("strategy", "mode"),
                fill_value=params.get("fill_value", "Unknown")
            )

        elif op == "convert_column_type":
            return PreprocessingEngine.convert_column_type(
                df, column=params.get("column", ""), target_type=params.get("target_type", "numeric")
            )

        elif op == "remove_outliers_iqr":
            return PreprocessingEngine.remove_outliers_iqr(
                df, column=params.get("column", ""), factor=params.get("factor", 1.5)
            )

        elif op == "drop_columns":
            return PreprocessingEngine.drop_columns(df, columns=params.get("columns", []))

        elif op == "scale_features":
            return PreprocessingEngine.scale_features(
                df, columns=params.get("columns", []), method=params.get("method", "minmax")
            )

        elif op == "log_transform":
            return PreprocessingEngine.log_transform(df, column=params.get("column", ""))

        elif op == "drop_missing":
            return PreprocessingEngine.drop_missing(
                df, axis=params.get("axis", "rows"), subset=params.get("subset")
            )

        else:
            return df, {"status": "unsupported_operation", "operation": op}

    @staticmethod
    def _attempt_adaptation(action: PlannedAction) -> bool:
        """Attempt to adjust parameters for self-correction when validation fails."""
        op = action.operation_name

        # Adaptation 1: If numerical imputation with mean failed, try median
        if op == "impute_missing_numeric":
            curr_strategy = action.parameters.get("strategy", "median")
            if curr_strategy == "mean":
                action.parameters["strategy"] = "median"
                return True
            elif curr_strategy == "median":
                action.parameters["strategy"] = "constant"
                action.parameters["fill_value"] = 0.0
                return True

        # Adaptation 2: If outlier removal with factor 1.5 dropped too many rows, relax to factor 2.5
        elif op == "remove_outliers_iqr":
            curr_factor = action.parameters.get("factor", 1.5)
            if curr_factor < 2.5:
                action.parameters["factor"] = 2.5
                return True

        return False

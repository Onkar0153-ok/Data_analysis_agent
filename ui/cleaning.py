"""Manual Data Cleaning Studio for DataPilot AI."""

import streamlit as st
import pandas as pd
from agent.state import SessionState
from data_engine.preprocessing import PreprocessingEngine
from storage.db import db_manager

def render_cleaning(state: SessionState):
    """Render manual data cleaning workspace with preview, undo, and reset capabilities."""
    st.markdown("## 🧹 Data Cleaning Workspace (Manual Mode)")
    st.markdown("Perform targeted, safe transformations on your dataset with live preview, undo, and rollback safeguards.")

    if state.current_df is None:
        st.info("No active dataset. Please upload or load a sample dataset in the Overview tab.")
        return

    df = state.current_df

    # Safety Controls: Undo and Reset
    col_u1, col_u2, col_info = st.columns([1, 1, 3])
    with col_u1:
        if st.button("↩️ Undo Last Change", disabled=(len(state.undo_stack) == 0), use_container_width=True):
            if state.undo_last_operation():
                st.success("Successfully reverted to previous snapshot!")
                st.rerun()

    with col_u2:
        if st.button("🔄 Reset to Original", use_container_width=True):
            state.reset_to_original()
            st.success("Dataset restored to pristine original upload!")
            st.rerun()

    with col_info:
        st.caption(f"Current dimensions: **{len(df)} rows &bull; {len(df.columns)} columns** | Snapshots in stack: **{len(state.undo_stack)}**")

    st.markdown("---")

    # Cleaning Operations Expander Sections
    # 1. Duplicates
    with st.expander("1. Remove Duplicate Rows", expanded=False):
        dup_count = int(df.duplicated().sum())
        st.write(f"Exact duplicate rows detected: **{dup_count}**")
        if dup_count > 0:
            if st.button("🗑️ Eliminate Duplicate Rows", key="manual_rm_dups"):
                state.push_snapshot("Manual remove duplicate rows")
                new_df, metrics = PreprocessingEngine.remove_duplicate_rows(df)
                state.update_after_mutation(new_df, "Manual duplicate removal")
                state.logger.log("MANUAL_OPERATION", metrics["impact"], status="SUCCESS")
                st.success(metrics["impact"])
                st.rerun()
        else:
            st.info("No duplicate rows to remove.")

    # 2. Text Normalization (Whitespace & Case)
    with st.expander("2. Text Normalization (Whitespace & Casing)", expanded=False):
        text_cols = [c for c in df.columns if df[c].dtype == object or pd.api.types.is_string_dtype(df[c])]
        if text_cols:
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown("##### Trim Whitespace")
                selected_trim = st.multiselect("Select columns to trim:", text_cols, default=text_cols)
                if st.button("✂️ Trim Whitespace", key="manual_trim"):
                    state.push_snapshot("Manual trim whitespace")
                    new_df, metrics = PreprocessingEngine.trim_whitespace(df, columns=selected_trim)
                    state.update_after_mutation(new_df, "Manual whitespace trim")
                    state.logger.log("MANUAL_OPERATION", metrics["impact"], status="SUCCESS")
                    st.success(metrics["impact"])
                    st.rerun()

            with col_t2:
                st.markdown("##### Standardize Case")
                target_case_cols = st.multiselect("Select columns for case formatting:", text_cols)
                case_style = st.selectbox("Case Style:", ["Title", "Lower", "Upper"])
                if st.button("🔤 Apply Case Format", key="manual_case") and target_case_cols:
                    state.push_snapshot(f"Manual case format to {case_style}")
                    new_df, metrics = PreprocessingEngine.normalize_text_case(df, target_case_cols, case_style=case_style.lower())
                    state.update_after_mutation(new_df, "Manual case standardization")
                    state.logger.log("MANUAL_OPERATION", metrics["impact"], status="SUCCESS")
                    st.success(metrics["impact"])
                    st.rerun()
        else:
            st.info("No text columns found.")

    # 3. Missing Value Imputation
    with st.expander("3. Missing Value Imputation", expanded=False):
        cols_with_null = [c for c in df.columns if df[c].isna().any()]
        if cols_with_null:
            imp_col = st.selectbox("Select column with missing values:", cols_with_null)
            is_numeric = pd.api.types.is_numeric_dtype(df[imp_col])
            
            if is_numeric:
                strategy = st.selectbox("Strategy:", ["median", "mean", "constant"])
                c_val = 0.0
                if strategy == "constant":
                    c_val = st.number_input("Constant Fill Value:", value=0.0)

                if st.button(f"📥 Impute {imp_col}", key="manual_imp_num"):
                    state.push_snapshot(f"Impute numeric {imp_col} with {strategy}")
                    new_df, metrics = PreprocessingEngine.impute_missing_numeric(df, imp_col, strategy=strategy, fill_value=c_val)
                    state.update_after_mutation(new_df, f"Impute {imp_col}")
                    state.logger.log("MANUAL_OPERATION", metrics["impact"], status="SUCCESS")
                    st.success(metrics["impact"])
                    st.rerun()
            else:
                strategy = st.selectbox("Strategy:", ["mode", "constant"])
                c_val = "Unknown"
                if strategy == "constant":
                    c_val = st.text_input("Constant Fill Value:", "Unknown")

                if st.button(f"📥 Impute {imp_col}", key="manual_imp_cat"):
                    state.push_snapshot(f"Impute categorical {imp_col} with {strategy}")
                    new_df, metrics = PreprocessingEngine.impute_missing_categorical(df, imp_col, strategy=strategy, fill_value=c_val)
                    state.update_after_mutation(new_df, f"Impute {imp_col}")
                    state.logger.log("MANUAL_OPERATION", metrics["impact"], status="SUCCESS")
                    st.success(metrics["impact"])
                    st.rerun()
        else:
            st.success("No missing values in current dataset.")

    # 4. Outlier Filtering (IQR)
    with st.expander("4. Statistical Outlier Removal (IQR)", expanded=False):
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if num_cols:
            out_col = st.selectbox("Select numeric column to inspect:", num_cols)
            factor = st.slider("IQR Multiplier Threshold:", min_value=1.0, max_value=3.0, value=1.5, step=0.1)

            # Preview outliers
            s = df[out_col].dropna()
            q25 = float(s.quantile(0.25))
            q75 = float(s.quantile(0.75))
            iqr = q75 - q25
            low_b = q25 - factor * iqr
            up_b = q75 + factor * iqr
            outlier_count = int(((s < low_b) | (s > up_b)).sum())

            st.write(f"Bounds: **[{low_b:.2f}, {up_b:.2f}]** &bull; Outliers detected: **{outlier_count}** ({outlier_count/len(s):.1%})")

            if outlier_count > 0:
                if st.button(f"⚠️ Filter {outlier_count} Outlier Rows in '{out_col}'", key="manual_rm_outliers", type="secondary"):
                    state.push_snapshot(f"Remove outliers in {out_col}")
                    new_df, metrics = PreprocessingEngine.remove_outliers_iqr(df, out_col, factor=factor)
                    state.update_after_mutation(new_df, f"Outlier removal {out_col}")
                    state.logger.log("MANUAL_OPERATION", metrics["impact"], status="SUCCESS")
                    st.success(metrics["impact"])
                    st.rerun()
        else:
            st.info("No numeric columns available.")

    # 5. Feature Scaling & Transformations
    with st.expander("5. Feature Scaling & Transformations", expanded=False):
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if num_cols:
            scale_cols = st.multiselect("Select columns to scale:", num_cols)
            scale_method = st.selectbox("Scaling Method:", ["minmax", "standard"], format_func=lambda x: "Min-Max [0, 1]" if x == "minmax" else "Z-Score (Standard)")
            if st.button("⚖️ Apply Scaling", key="manual_scale") and scale_cols:
                state.push_snapshot(f"Scale {scale_cols} with {scale_method}")
                new_df, metrics = PreprocessingEngine.scale_features(df, scale_cols, method=scale_method)
                state.update_after_mutation(new_df, f"Scaling {scale_cols}")
                state.logger.log("MANUAL_OPERATION", metrics["impact"], status="SUCCESS")
                st.success(metrics["impact"])
                st.rerun()

            st.markdown("---")
            log_col = st.selectbox("Select column for Log1p Transformation (strictly non-negative):", num_cols)
            if st.button(f"📐 Apply Log1p to '{log_col}'", key="manual_log"):
                state.push_snapshot(f"Log transform {log_col}")
                new_df, metrics = PreprocessingEngine.log_transform(df, log_col)
                if metrics.get("status") == "rejected_unsafe":
                    st.error(metrics.get("reason"))
                else:
                    state.update_after_mutation(new_df, f"Log transform {log_col}")
                    state.logger.log("MANUAL_OPERATION", metrics["impact"], status="SUCCESS")
                    st.success(metrics["impact"])
                    st.rerun()

    # 6. Drop Columns
    with st.expander("6. Drop Columns", expanded=False):
        cols_to_drop = st.multiselect("Select columns to permanently remove from dataset:", list(df.columns))
        if cols_to_drop:
            st.warning(f"⚠️ You have selected {len(cols_to_drop)} column(s) to drop.")
            if st.button("❌ Confirm Drop Columns", key="manual_drop_cols"):
                state.push_snapshot(f"Drop columns {cols_to_drop}")
                new_df, metrics = PreprocessingEngine.drop_columns(df, cols_to_drop)
                state.update_after_mutation(new_df, "Drop columns")
                state.logger.log("MANUAL_OPERATION", metrics["impact"], status="SUCCESS")
                st.success(metrics["impact"])
                st.rerun()

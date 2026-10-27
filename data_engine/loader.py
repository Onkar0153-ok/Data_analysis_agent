"""Dataset ingestion and loading module for DataPilot AI."""

import os
import io
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import numpy as np

from config.settings import MAX_UPLOAD_SIZE_MB, SUPPORTED_EXTENSIONS, SAMPLE_DATA_PATH

logger = logging.getLogger(__name__)

class DatasetLoader:
    """Robust dataset loader supporting CSV, TSV, and XLSX with encoding & delimiter handling."""

    @staticmethod
    def get_supported_extensions() -> List[str]:
        return SUPPORTED_EXTENSIONS

    @staticmethod
    def load_from_file(file_obj_or_path: Any, filename: str, sheet_name: Optional[str] = None) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """Load a dataset from an uploaded file object or a local file path.
        
        Returns:
            (df, metadata_dict)
        """
        metadata: Dict[str, Any] = {
            "filename": filename,
            "success": False,
            "error": None,
            "encoding": "utf-8",
            "delimiter": ",",
            "sheet_names": [],
            "selected_sheet": sheet_name,
            "empty_rows_dropped": 0,
            "empty_cols_dropped": 0,
            "original_shape": (0, 0),
            "final_shape": (0, 0),
            "duplicate_col_names": [],
            "warnings": [],
        }

        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            metadata["error"] = f"Unsupported file extension '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            return None, metadata

        # Check file size if it's a file path
        if isinstance(file_obj_or_path, (str, Path)):
            file_path = Path(file_obj_or_path)
            if not file_path.exists():
                metadata["error"] = f"File not found: {file_path}"
                return None, metadata
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > MAX_UPLOAD_SIZE_MB:
                metadata["error"] = f"File size ({size_mb:.1f} MB) exceeds maximum allowed ({MAX_UPLOAD_SIZE_MB} MB)."
                return None, metadata

        df: Optional[pd.DataFrame] = None

        try:
            if ext in [".csv", ".tsv"]:
                df, metadata = DatasetLoader._load_delimited(file_obj_or_path, ext, metadata)
            elif ext == ".xlsx":
                df, metadata = DatasetLoader._load_excel(file_obj_or_path, sheet_name, metadata)

            if df is None or df.empty:
                metadata["error"] = metadata.get("error") or "Dataset is empty or contains no records."
                return None, metadata

            # Clean and normalize columns and missing markers
            df, metadata = DatasetLoader._clean_and_normalize(df, metadata)
            metadata["success"] = True
            metadata["final_shape"] = df.shape
            return df, metadata

        except Exception as e:
            logger.exception("Error loading dataset %s", filename)
            metadata["error"] = f"Failed to parse file: {str(e)}"
            return None, metadata

    @staticmethod
    def _load_delimited(file_obj_or_path: Any, ext: str, metadata: Dict[str, Any]) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """Load CSV/TSV with encoding detection and delimiter fallback."""
        default_delim = "\t" if ext == ".tsv" else ","
        encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]
        delimiters = [default_delim, ",", "\t", ";", "|"]
        
        # Read raw bytes to allow multi-try decoding
        if hasattr(file_obj_or_path, "read"):
            content_bytes = file_obj_or_path.read()
            if hasattr(file_obj_or_path, "seek"):
                file_obj_or_path.seek(0)
        else:
            with open(file_obj_or_path, "rb") as f:
                content_bytes = f.read()

        if len(content_bytes) == 0:
            metadata["error"] = "File is 0 bytes."
            return None, metadata

        last_error = None
        for enc in encodings:
            for delim in delimiters:
                try:
                    stream = io.BytesIO(content_bytes)
                    # Attempt reading a sample chunk first
                    df = pd.read_csv(
                        stream,
                        sep=delim,
                        encoding=enc,
                        na_values=["N/A", "NA", "null", "NULL", "None", "none", "?", "-", ""],
                        keep_default_na=True,
                        low_memory=False
                    )
                    # Plausibility check: should have more than 1 column or 1 row
                    if df.shape[1] > 1 or (df.shape[1] == 1 and df.shape[0] > 0 and delim == default_delim):
                        metadata["encoding"] = enc
                        metadata["delimiter"] = delim
                        return df, metadata
                except Exception as ex:
                    last_error = ex
                    continue

        metadata["error"] = f"Unable to parse delimited text: {last_error}"
        return None, metadata

    @staticmethod
    def _load_excel(file_obj_or_path: Any, sheet_name: Optional[str], metadata: Dict[str, Any]) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """Load Excel workbook and handle sheet selection."""
        excel_file = pd.ExcelFile(file_obj_or_path, engine="openpyxl")
        metadata["sheet_names"] = excel_file.sheet_names
        
        target_sheet = sheet_name if (sheet_name and sheet_name in excel_file.sheet_names) else excel_file.sheet_names[0]
        metadata["selected_sheet"] = target_sheet

        df = pd.read_excel(
            excel_file,
            sheet_name=target_sheet,
            na_values=["N/A", "NA", "null", "NULL", "None", "none", "?", "-", ""],
            keep_default_na=True
        )
        return df, metadata

    @staticmethod
    def _clean_and_normalize(df: pd.DataFrame, metadata: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Normalize empty cells, detect duplicate column names, and remove all-empty rows/cols."""
        metadata["original_shape"] = df.shape

        # 1. Normalize column names: strip strings, convert unnamed/empty
        raw_cols = [str(c).strip() if pd.notna(c) else "unnamed_column" for c in df.columns]
        
        # Detect duplicates and disambiguate
        seen_cols = {}
        cleaned_cols = []
        dup_cols = []
        for col in raw_cols:
            if col in seen_cols:
                seen_cols[col] += 1
                new_col = f"{col}_{seen_cols[col]}"
                cleaned_cols.append(new_col)
                dup_cols.append(col)
            else:
                seen_cols[col] = 0
                cleaned_cols.append(col)
        
        df.columns = cleaned_cols
        if dup_cols:
            metadata["duplicate_col_names"] = list(set(dup_cols))
            metadata["warnings"].append(f"Renamed duplicate columns: {', '.join(set(dup_cols))}")

        # 2. Drop completely empty rows and columns
        initial_rows, initial_cols = df.shape
        df = df.dropna(how="all", axis=0)
        rows_dropped = initial_rows - len(df)
        metadata["empty_rows_dropped"] = rows_dropped

        df = df.dropna(how="all", axis=1)
        cols_dropped = initial_cols - len(df.columns)
        metadata["empty_cols_dropped"] = cols_dropped

        if rows_dropped > 0:
            metadata["warnings"].append(f"Removed {rows_dropped} completely empty row(s).")
        if cols_dropped > 0:
            metadata["warnings"].append(f"Removed {cols_dropped} completely empty column(s).")

        return df, metadata

    @staticmethod
    def load_sample_dataset() -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """Load the bundled demo sales dataset."""
        if not SAMPLE_DATA_PATH.exists():
            return None, {"success": False, "error": f"Sample dataset not found at {SAMPLE_DATA_PATH}"}
        return DatasetLoader.load_from_file(str(SAMPLE_DATA_PATH), "sample_sales.csv")

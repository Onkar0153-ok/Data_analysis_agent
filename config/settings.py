"""Configuration and global settings for DataPilot AI."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
SAMPLE_DATA_PATH = SAMPLE_DATA_DIR / "sample_sales.csv"

# Storage Settings
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "datapilot.db"))
PERSIST_DATASETS = os.getenv("PERSIST_DATASETS", "false").lower() in ("true", "1", "yes")

# Ingestion limits
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
SUPPORTED_EXTENSIONS = [".csv", ".tsv", ".xlsx"]

# UI & Theme Palette
THEME = {
    "bg_main": "#0B1220",
    "bg_sidebar": "#111827",
    "bg_panel": "#141F32",
    "bg_card": "#1E293B",
    "accent_primary": "#22D3EE",      # Cyan
    "accent_secondary": "#60A5FA",    # Blue
    "accent_hover": "#38BDF8",
    "text_main": "#F8FAFC",
    "text_muted": "#94A3B8",
    "border": "#273449",
    "warning": "#F59E0B",            # Amber
    "error": "#EF4444",              # Red
    "success": "#10B981",            # Teal/Green
    "info": "#38BDF8",
}

# Quality Score Weights (Total 100)
# Measurable indicators:
# 1. Completeness (Missing values rate): 35 points
# 2. Uniqueness (Exact duplicate rows rate): 25 points
# 3. Data Type & Schema Integrity: 20 points
# 4. Consistency (Text whitespace & outliers rate): 20 points
QUALITY_WEIGHTS = {
    "completeness": 35.0,
    "uniqueness": 25.0,
    "type_integrity": 20.0,
    "consistency": 20.0,
}

# Risk Levels for Operations
class RiskLevel:
    SAFE = "SAFE"
    REVIEW_RECOMMENDED = "REVIEW RECOMMENDED"
    HIGH_RISK = "HIGH RISK"

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

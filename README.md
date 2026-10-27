# DataPilot AI ✈️
### Autonomous AI Agent for Intelligent Data Analysis, Visualization, and Data Preparation

---

## 📌 Project Overview
**DataPilot AI** is an autonomous AI agent application engineered for tabular data understanding, automated data preparation, interactive visual analytics, and conversational intelligence. 

Built specifically as an AI Agents subject mini-project for college presentation and viva demonstration, DataPilot AI exhibits genuine autonomous agent behaviors (**Perceive &rarr; Plan &rarr; Act &rarr; Validate &rarr; Adapt &rarr; Report**) rather than functioning merely as a static dashboard or superficial chatbot wrapper.

---

## 🌟 Key Capabilities & Features

### 1. Robust Dataset Ingestion & Auto-Detection
- Supports **CSV**, **TSV**, and **XLSX** (Excel) files with automated sheet selection.
- Multi-encoding fallback (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`, `iso-8859-1`).
- Delimiter detection (comma, tab, semicolon, pipe).
- Normalization of missing indicators (`N/A`, `null`, `None`, `?`, `-`, whitespace).
- Duplicate column header detection and automatic disambiguation.
- Packaged with a realistic **Sample Sales Dataset** featuring controlled issues (missing values, duplicate rows, whitespace errors, case inconsistencies, and extreme outliers).

### 2. Autonomous Agent Lifecycle (AutoPilot Mode)
- **Stage 1 (Perception):** Analyzes dataset dimensions, infers semantic types (Numeric Continuous, Discrete, Categorical, Datetime, Identifier, Boolean), detects missing values, duplicate records, text casing inconsistencies, whitespace flaws, and statistical outliers.
- **Stage 2 (Planning):** Uses a transparent Python decision engine to formulate a prioritized, dependency-ordered cleaning plan with explicit Action IDs, reasoning, and risk levels.
- **Stage 3 (Risk-Aware Execution):**
  - **SAFE:** Trim whitespace, standardize category casing, remove exact duplicates.
  - **REVIEW RECOMMENDED:** Numerical & categorical imputation, data type conversions, feature scaling.
  - **HIGH RISK:** Statistical outlier deletion (1.5*IQR), column dropping. Always requires explicit user confirmation.
- **Stage 4 (Execution):** Captures pre-execution snapshots before every mutation.
- **Stage 5 (Validation):** Evaluates post-condition gates (ensuring no corrupted conversions, plausible row counts, and resolution of targeted issues).
- **Stage 6 (Adaptation & Rollback):** Automatically reverts to previous valid snapshot if validation criteria fail, adjusts parameters (bounded retries up to 2 attempts), and prevents infinite retry loops.
- **Stage 7 (Reporting):** Compiles transformation manifests and calculates before-and-after quality deltas.

### 3. Explainable Data Quality Score (0–100)
- Fully transparent heuristic formula scoring across 4 measurable dimensions:
  1. **Completeness (35 pts):** Absence of missing/null cells.
  2. **Uniqueness (25 pts):** Absence of duplicate rows.
  3. **Type Integrity (20 pts):** Semantic type validity and absence of constant columns.
  4. **Consistency (20 pts):** Text whitespace hygiene, category casing, and IQR outlier boundaries.
- Assigns letter grades (A, B, C, D, F) with transparent point breakdowns.

### 4. Interactive Visual Analytics Engine
- **Automated Recommendations:** Automatically synthesizes Plotly charts based on dataset characteristics:
  - Missing Value Frequency Bar Chart
  - Pairwise Pearson Correlation Heatmap
  - Category Frequency Distributions
  - Distribution Histograms with Outlier Box Plots
  - Bivariate Scatter Plots with Trendlines
  - Chronological Time Series Line Charts
- **Custom Chart Studio:** Build interactive custom visualizations (Bar, Line, Scatter, Histogram, Box, Pie) with customizable X/Y axes, color grouping, and aggregations.

### 5. LLM-Powered "Ask Your Data"
- Conversational analysis grounded in real Pandas computation via controlled tool/function calling.
- **Tools Implemented:**
  - `get_dataset_summary`
  - `get_column_profile`
  - `get_missing_value_report`
  - `get_duplicate_report`
  - `get_top_bottom_values`
  - `calculate_aggregation`
  - `calculate_correlation`
  - `detect_outliers`
  - `filter_dataset`
  - `compare_groups`
  - `get_quality_report`
  - `create_chart`
- **Zero-Hallucination & Privacy Protection:** Raw dataset records are never transmitted to the LLM. Only schemas and targeted tool computation results are processed.
- **Deterministic Offline Fallback:** If no API key is supplied, an integrated rule-based natural language parser answers summaries, aggregations, correlations, missing value queries, and chart requests locally.

### 6. Persistent Storage (SQLite)
- Local SQLite database (`datapilot.db`) created automatically on first launch.
- Persists session metadata, agent activity logs, cleaning manifests, and chat history.
- History view allows reviewing past sessions, replaying operation manifests with schema validation, or deleting records.

### 7. Executive Reporting & Manifest Replay
- Download cleaned dataset as CSV.
- Download standalone executive HTML analysis report with before/after audit metrics.
- Export reproducible JSON operation manifest and replay it on new datasets.

---

## 📂 Project Architecture

```
DataPilot-AI/
├── app.py                      # Main Streamlit web application & router
├── requirements.txt            # Minimal, stable Python dependencies
├── README.md                   # Comprehensive documentation & presentation guide
├── .env.example                # Template for environment configuration
├── .gitignore                  # Git ignore rules
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Themes, weights, upload limits, risk definitions
│
├── storage/
│   ├── __init__.py
│   └── db.py                   # SQLite database manager & parameterized query interface
│
├── agent/
│   ├── __init__.py
│   ├── models.py               # Data models (PlannedAction, AgentEvent, ActionStatus)
│   ├── policies.py             # Risk classification & auto-execution policies
│   ├── planner.py              # Autonomous perception & plan generation
│   ├── validator.py            # Rigorous post-execution validation gates
│   ├── executor.py             # Execution dispatch, snapshot rollback & adaptation
│   ├── activity_log.py         # Chronological event logger
│   └── state.py                # Working dataset state, undo stack & snapshot management
│
├── data_engine/
│   ├── __init__.py
│   ├── loader.py               # CSV/TSV/XLSX loader with encoding & delimiter fallback
│   ├── profiler.py             # Deep profiling, semantic types & issue perception
│   ├── quality_score.py        # Explainable 0-100 heuristic scoring engine
│   ├── preprocessing.py        # Predefined, deterministic transformation methods
│   ├── visualization.py        # Plotly chart recommendations & custom studio
│   └── comparison.py           # Before-and-after audit calculations
│
├── llm/
│   ├── __init__.py
│   ├── tool_definitions.py     # JSON declarations for function calling
│   ├── tool_executor.py        # Safe Pandas execution for tool queries
│   ├── fallback.py             # Offline deterministic question parser
│   ├── prompts.py              # System prompts & grounding rules
│   └── client.py               # Google Gemini client with tool calling & fallback
│
├── ui/
│   ├── __init__.py
│   ├── styles.py               # Dark analytics CSS design system
│   ├── overview.py             # Ingestion & health profile page
│   ├── explorer.py             # Raw data & column inspector page
│   ├── autopilot.py            # Autonomous agent plan & live decision trace
│   ├── visualizations.py       # Recommended & custom charts page
│   ├── ask_data.py             # Conversational data chat page
│   ├── cleaning.py             # Manual cleaning studio page
│   ├── reports.py              # Reports, exports & manifest replay page
│   ├── history_view.py         # SQLite session history viewer
│   └── settings_view.py        # API key test & policy switches page
│
├── utils/
│   ├── __init__.py
│   ├── validation.py           # Schema matching & manifest validator
│   ├── export.py               # Standalone HTML report & manifest replayer
│   └── logging_config.py       # Console logging setup
│
├── sample_data/
│   └── sample_sales.csv        # Realistic demonstration dataset with controlled issues
│
└── tests/
    ├── __init__.py
    ├── test_loader.py          # Loader tests
    ├── test_profiler.py        # Profiler & semantic type tests
    ├── test_preprocessing.py   # Transformation engine tests
    ├── test_agent.py           # Agent planning, validation & rollback tests
    ├── test_llm_tools.py       # Tool executor & fallback parser tests
    ├── test_visualization.py   # Plotly chart generation tests
    └── test_storage.py         # SQLite persistence tests
```

---

## 🚀 Installation and Local Execution

### Prerequisites
- Python 3.11 or 3.12 installed on your machine.
- Windows PowerShell, macOS Terminal, or Linux Bash.

### Setup Steps (Windows PowerShell)

1. **Clone or navigate into the project directory:**
   ```powershell
   cd c:\Users\RD\OneDrive\Desktop\Ai-Agent_data_analysis
   ```

2. **(Optional) Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **(Optional) Configure Gemini API Key:**
   Copy the example environment file:
   ```powershell
   Copy-Item .env.example .env
   ```
   Open `.env` in any text editor and supply your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
   *(Note: You can also enter the API key directly within the app under Settings, or skip it entirely to run in deterministic offline fallback mode).*

5. **Run automated test suite:**
   ```powershell
   pytest -v
   ```
   *(All 21 automated tests will execute and verify the entire backend, profiler, transformations, and SQLite persistence).*

6. **Launch DataPilot AI:**
   ```powershell
   streamlit run app.py
   ```
   The application will launch and open in your default browser at `http://localhost:8501`.

---

## 🎓 Viva & Presentation Demonstration Guide

When presenting DataPilot AI during a college project review or viva, follow this structured demonstration flow:

### Step 1: Demonstrate Ingestion & Automatic Perception
1. Open the application at `http://localhost:8501`.
2. On the **📊 Overview** tab, click **🚀 Load Sample Sales Dataset (Demo)**.
3. Highlight the immediate calculation of the **Heuristic Quality Score** (e.g. ~74.5/100, Grade C), **Missing Cells**, **Duplicate Rows**, and **Perceived Issues**.
4. Expand the **Quality Breakdown** to explain the 4 measurable scoring dimensions (Completeness, Uniqueness, Type Integrity, Consistency).

### Step 2: Show Automatic Semantic Profiling
1. Click **🔎 Data Explorer** in the sidebar.
2. Under **📊 Column Profiles**, select `Order_ID`. Show that the agent correctly identified it as an **IDENTIFIER** rather than misclassifying it as continuous numeric data.
3. Select `Category` or `Region`. Show the detection of text casing inconsistencies (e.g. 'North' vs 'north') and leading/trailing whitespace.

### Step 3: Demonstrate Genuine Agent AutoPilot Behavior
1. Navigate to **🤖 AutoPilot Agent**.
2. Click **🧠 Formulate Plan**. Explain to the examiners that the agent:
   - Does not blindly execute a hardcoded script.
   - Orders actions by dependency (whitespace &rarr; casing &rarr; deduplication &rarr; missing value imputation &rarr; outlier review).
   - Classifies actions by risk: **SAFE** (green), **REVIEW** (amber), and **HIGH RISK** (red).
3. Click **⚡ Execute Safe** to automatically execute safe operations.
4. Show how the **Live Agent Decision Trace** on the right logs every execution and validation result in real time.
5. Demonstrate single-step execution and approval for missing value imputation and outliers. Show how the quality score updates to ~95+/100 (Grade A).

### Step 4: Demonstrate Safety, Undo & Rollback
1. Go to **🧹 Data Cleaning**.
2. Perform a manual operation (e.g. drop a column or scale features).
3. Click **↩️ Undo Last Change** in the sidebar or page to prove the snapshot rollback mechanism works reliably without corrupting the dataset.

### Step 5: Demonstrate Visual Analytics
1. Navigate to **📈 Visualizations**.
2. Show the **Recommended Charts** tab:
   - Missing values bar chart
   - Correlation heatmap across numeric measures
   - Distribution histogram with box plots
   - Time-series trendlines
3. Show the **Custom Chart Studio** by building an interactive bar chart of `Revenue` grouped by `Region`.

### Step 6: Demonstrate "Ask Your Data" LLM Tool Calling
1. Navigate to **💬 Ask Your Data**.
2. Point out the provider status banner (**Gemini Function Calling** if key is present, or **Deterministic Fallback** if offline).
3. Click quick question buttons such as:
   - *"Which region has the highest average revenue?"*
   - *"What is the correlation between price and revenue?"*
   - *"Which columns have the most missing values?"*
4. Explain to the examiner that the LLM did not invent numbers: it selected the controlled `calculate_aggregation` tool, Pandas performed the actual math, and the LLM synthesized the grounded explanation with an interactive chart.

### Step 7: Demonstrate Persistent Audit & Exports
1. Navigate to **📑 Reports & Exports**.
2. Download the cleaned CSV dataset and the standalone **HTML Audit Report**.
3. Point out the **Operation Manifest (JSON)** and explain how it enables automated reproduction on future datasets.
4. Navigate to **📜 History & Sessions** to show that session metadata, agent activity, and cleaning manifests are persistently stored in SQLite.

---

## 🔒 Security & Privacy Guarantees
- **No Private Data Leaks:** Uploaded raw datasets are processed locally in memory. Only dataset schemas and targeted tool computation summaries are sent to the LLM.
- **No Arbitrary Code Execution:** The LLM cannot execute arbitrary shell commands, raw SQL, or unchecked Python scripts. Every action is dispatched through pre-validated Python methods.
- **Safe Credential Handling:** API keys are never stored in the database, log files, or exported reports.

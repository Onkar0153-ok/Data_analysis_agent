"""Custom CSS and dark analytics theme styles for DataPilot AI."""

def get_custom_css() -> str:
    return """
    <style>
        /* Global App Styling */
        .stApp {
            background-color: #0B1220;
            color: #F8FAFC;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #111827;
            border-right: 1px solid #273449;
        }

        section[data-testid="stSidebar"] .stMarkdown h1,
        section[data-testid="stSidebar"] .stMarkdown h2,
        section[data-testid="stSidebar"] .stMarkdown h3 {
            color: #22D3EE;
        }

        /* Metric Cards */
        .datapilot-card {
            background: #141F32;
            border: 1px solid #273449;
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            transition: border-color 0.2s ease;
        }
        .datapilot-card:hover {
            border-color: #22D3EE;
        }

        .metric-title {
            color: #94A3B8;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }

        .metric-value {
            color: #F8FAFC;
            font-size: 26px;
            font-weight: 700;
        }

        .metric-sub {
            color: #38BDF8;
            font-size: 12px;
            margin-top: 4px;
        }

        /* Risk Badges */
        .badge-safe {
            background-color: rgba(16, 185, 129, 0.15);
            color: #10B981;
            border: 1px solid #10B981;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        .badge-review {
            background-color: rgba(245, 158, 11, 0.15);
            color: #F59E0B;
            border: 1px solid #F59E0B;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        .badge-high-risk {
            background-color: rgba(239, 68, 68, 0.15);
            color: #EF4444;
            border: 1px solid #EF4444;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        /* Timeline and Log Entries */
        .event-entry {
            background: #111827;
            border-left: 3px solid #22D3EE;
            padding: 10px 14px;
            margin-bottom: 8px;
            border-radius: 0 6px 6px 0;
            font-size: 13px;
        }

        .event-time {
            color: #94A3B8;
            font-size: 11px;
            margin-right: 8px;
        }

        /* Buttons Styling */
        div.stButton > button {
            background-color: #1E293B;
            color: #F8FAFC;
            border: 1px solid #273449;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        div.stButton > button:hover {
            border-color: #22D3EE;
            color: #22D3EE;
            background-color: #141F32;
        }

        div.stButton > button[kind="primary"] {
            background-color: #0284C7;
            color: #FFFFFF;
            border: 1px solid #38BDF8;
        }

        div.stButton > button[kind="primary"]:hover {
            background-color: #0369A1;
            border-color: #22D3EE;
        }

        /* Header Accent */
        h1, h2, h3 {
            color: #F8FAFC;
            letter-spacing: -0.02em;
        }
        
        .header-accent {
            color: #22D3EE;
        }

        /* DataTables container */
        div[data-testid="stDataFrame"] {
            background-color: #111827;
            border: 1px solid #273449;
            border-radius: 8px;
        }
    </style>
    """

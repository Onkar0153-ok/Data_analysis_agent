"""Function calling tool definitions and schemas for DataPilot AI."""

from typing import List, Dict, Any

# Declarative schema for tool calls compatible with LLM providers
TOOL_DECLARATIONS = [
    {
        "name": "get_dataset_summary",
        "description": "Get high-level summary of the dataset including dimensions, column names, semantic types, and overall missing values.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_column_profile",
        "description": "Get detailed statistics, data type, unique count, missing count, and sample distribution for a specific column.",
        "parameters": {
            "type": "object",
            "properties": {
                "column_name": {"type": "string", "description": "The exact name of the column to profile."}
            },
            "required": ["column_name"]
        }
    },
    {
        "name": "get_missing_value_report",
        "description": "Get a detailed breakdown of all columns containing missing (null) values with counts and percentages.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_duplicate_report",
        "description": "Check for exact duplicate rows in the dataset and report count and percentage.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_top_bottom_values",
        "description": "Retrieve the top or bottom N records sorted by a specific numerical or ordered column.",
        "parameters": {
            "type": "object",
            "properties": {
                "column_name": {"type": "string", "description": "The numeric column to sort by."},
                "n": {"type": "integer", "description": "Number of records to return (default: 5, max: 20)."},
                "order": {"type": "string", "enum": ["top", "bottom"], "description": "Whether to return highest (top) or lowest (bottom) values."}
            },
            "required": ["column_name"]
        }
    },
    {
        "name": "calculate_aggregation",
        "description": "Aggregate a numeric column grouped by a categorical column (e.g. average revenue by region).",
        "parameters": {
            "type": "object",
            "properties": {
                "group_by_column": {"type": "string", "description": "Categorical column to group by."},
                "metric_column": {"type": "string", "description": "Numeric column to aggregate."},
                "agg_func": {
                    "type": "string",
                    "enum": ["mean", "sum", "median", "count", "min", "max"],
                    "description": "Aggregation function to apply (default: 'mean')."
                }
            },
            "required": ["group_by_column", "metric_column"]
        }
    },
    {
        "name": "calculate_correlation",
        "description": "Compute the Pearson correlation coefficient between two numeric columns.",
        "parameters": {
            "type": "object",
            "properties": {
                "col1": {"type": "string", "description": "First numeric column."},
                "col2": {"type": "string", "description": "Second numeric column."}
            },
            "required": ["col1", "col2"]
        }
    },
    {
        "name": "detect_outliers",
        "description": "Detect statistical outliers in a numeric column using the Interquartile Range (IQR) method.",
        "parameters": {
            "type": "object",
            "properties": {
                "column_name": {"type": "string", "description": "The numeric column to examine for outliers."}
            },
            "required": ["column_name"]
        }
    },
    {
        "name": "filter_dataset",
        "description": "Filter dataset rows by condition and return count and summary statistics.",
        "parameters": {
            "type": "object",
            "properties": {
                "column_name": {"type": "string", "description": "Column to filter on."},
                "operator": {"type": "string", "enum": [">", "<", "==", "!=", ">=", "<="], "description": "Comparison operator."},
                "value": {"type": "string", "description": "Value to compare against (numeric or string)."}
            },
            "required": ["column_name", "operator", "value"]
        }
    },
    {
        "name": "compare_groups",
        "description": "Compare summary statistics (mean, median, std, count) of a metric across categories.",
        "parameters": {
            "type": "object",
            "properties": {
                "group_column": {"type": "string", "description": "Categorical grouping column."},
                "metric_column": {"type": "string", "description": "Numeric metric column."}
            },
            "required": ["group_column", "metric_column"]
        }
    },
    {
        "name": "get_quality_report",
        "description": "Get current DataPilot Heuristic Data Quality score (0-100), grade, and breakdown across dimensions.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "create_chart",
        "description": "Recommend or generate an interactive chart to visualize data requested by user.",
        "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {"type": "string", "enum": ["bar", "line", "scatter", "histogram", "box", "pie"], "description": "Type of chart."},
                "x_column": {"type": "string", "description": "Column for X axis."},
                "y_column": {"type": "string", "description": "Column for Y axis (optional for histograms/pies)."},
                "title": {"type": "string", "description": "Chart title."}
            },
            "required": ["chart_type", "x_column"]
        }
    }
]

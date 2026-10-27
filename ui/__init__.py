"""UI package for DataPilot AI."""

from ui.styles import get_custom_css
from ui.overview import render_overview
from ui.explorer import render_explorer
from ui.autopilot import render_autopilot
from ui.visualizations import render_visualizations
from ui.ask_data import render_ask_data
from ui.cleaning import render_cleaning
from ui.reports import render_reports
from ui.history_view import render_history_view
from ui.settings_view import render_settings

__all__ = [
    "get_custom_css",
    "render_overview",
    "render_explorer",
    "render_autopilot",
    "render_visualizations",
    "render_ask_data",
    "render_cleaning",
    "render_reports",
    "render_history_view",
    "render_settings",
]

"""
U1: Theme Manager - Dark mode support for dashboard.

Provides light/dark theme switching with consistent color palettes
for the entire dashboard UI.
"""

import streamlit as st
from typing import Literal, Dict, Any

ThemeMode = Literal["light", "dark"]

# Color palettes for both themes
COLORS: Dict[str, Dict[str, str]] = {
    "light": {
        "bg": "#FFFFFF",
        "sidebar": "#F0F2F6",
        "text": "#1F1F1F",
        "text_secondary": "#5C5C5C",
        "accent": "#FF4B4B",
        "chart_bg": "#FFFFFF",
        "grid_lines": "#E0E0E0",
        "chart_template": "plotly_white",
    },
    "dark": {
        "bg": "#0E1117",
        "sidebar": "#262730",
        "text": "#FAFAFA",
        "text_secondary": "#A0A0A0",
        "accent": "#FF4B4B",
        "chart_bg": "#111111",
        "grid_lines": "#333333",
        "chart_template": "plotly_dark",
    }
}


def init_theme() -> None:
    """
    Initialize theme state in session_state.

    Call this once at the start of the app, after st.set_page_config().
    """
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False


def get_theme() -> ThemeMode:
    """
    Get current theme mode.

    Returns:
        "dark" if dark mode is enabled, "light" otherwise.
    """
    return "dark" if st.session_state.get("dark_mode", False) else "light"


def get_colors() -> Dict[str, str]:
    """
    Get color palette for current theme.

    Returns:
        Dict with color values for current theme mode.
    """
    return COLORS[get_theme()]


def render_theme_toggle() -> bool:
    """
    Render theme toggle in sidebar.

    Creates a toggle switch that allows users to switch between
    light and dark modes.

    Returns:
        Current dark mode state (True = dark, False = light).
    """
    dark_mode = st.sidebar.toggle(
        "Dark Mode",
        value=st.session_state.get("dark_mode", False),
        key="dark_mode_toggle",
        help="Switch between light and dark theme"
    )
    st.session_state.dark_mode = dark_mode
    return dark_mode


def apply_custom_css() -> None:
    """
    Apply custom CSS based on current theme.

    Injects CSS that styles the application according to the
    current theme's color palette. Should be called after
    render_theme_toggle() to ensure theme state is current.
    """
    colors = get_colors()
    is_dark = get_theme() == "dark"

    # Additional dark mode specific styles
    dark_specific = ""
    if is_dark:
        dark_specific = """
        /* Dark mode specific overrides */
        .stDataFrame {
            background-color: #1a1a2e;
        }
        .stDataFrame th {
            background-color: #262730 !important;
            color: #FAFAFA !important;
        }
        .stDataFrame td {
            color: #FAFAFA !important;
        }
        /* Tabs styling */
        .stTabs [role="tab"] {
            color: #A0A0A0;
        }
        .stTabs [aria-selected="true"] {
            color: #FAFAFA !important;
        }
        /* Metric styling */
        .stMetric > div > label {
            color: #A0A0A0 !important;
        }
        .stMetric > div > div {
            color: #FAFAFA !important;
        }
        """

    st.markdown(f"""
    <style>
        /* Main background */
        .stApp {{
            background-color: {colors['bg']};
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {colors['sidebar']};
        }}

        /* Text colors */
        .stMarkdown, .stMetric label {{
            color: {colors['text']};
        }}

        /* KPI Card styling */
        .kpi-card {{
            background-color: {colors['sidebar']};
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        /* Section headers */
        h1, h2, h3 {{
            color: {colors['text']};
        }}

        /* Caption and secondary text */
        .stCaption, small {{
            color: {colors['text_secondary']};
        }}

        /* Download button styling */
        .stDownloadButton button {{
            background-color: {colors['accent']};
            color: white;
        }}

        /* DataFrame header background */
        .stDataFrame th {{
            background-color: {colors['sidebar']};
        }}

        {dark_specific}
    </style>
    """, unsafe_allow_html=True)

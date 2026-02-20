"""
U1: Theme Manager - Dark mode support for dashboard.

Provides CSS-based dark mode that can be toggled at runtime.
"""

import streamlit as st
from typing import Literal, Dict

ThemeMode = Literal["light", "dark"]

# Color palettes for charts
CHART_COLORS: Dict[str, Dict[str, str]] = {
    "light": {
        "chart_template": "plotly_white",
        "primary": "#1f77b4",
        "secondary": "#ff7f0e",
        "accent": "#FF4B4B",
    },
    "dark": {
        "chart_template": "plotly_dark",
        "primary": "#4da6ff",
        "secondary": "#ffaa00",
        "accent": "#FF6B6B",
    }
}


def init_theme() -> None:
    """
    Initialize theme state in session_state.

    Call this once at the start of the app, after st.set_page_config().
    """
    if "dark_mode" not in st.session_state:
        # Try to detect from st.context.theme.base (Streamlit 1.40+)
        try:
            detected = st.context.theme.base == "dark"
            st.session_state.dark_mode = detected
        except AttributeError:
            st.session_state.dark_mode = False


def get_theme() -> ThemeMode:
    """
    Get current theme mode.

    Returns:
        "dark" if dark mode is enabled, "light" otherwise.
    """
    if st.session_state.get("dark_mode", False):
        return "dark"
    return "light"


def get_colors() -> Dict[str, str]:
    """
    Get color palette for current theme.

    Returns:
        Dict with color values for current theme mode.
    """
    return CHART_COLORS[get_theme()]


def render_theme_toggle() -> bool:
    """
    Render theme toggle in sidebar.

    Creates a toggle switch that allows users to switch between
    light and dark modes.

    Returns:
        Current dark mode state (True = dark, False = light).
    """
    dark_mode = st.sidebar.toggle(
        "🌙 Dark Mode",
        value=st.session_state.get("dark_mode", False),
        key="dark_mode_toggle",
        help="Switch between light and dark theme"
    )

    # Update session state if changed
    if dark_mode != st.session_state.get("dark_mode", False):
        st.session_state.dark_mode = dark_mode
        st.rerun()

    return dark_mode


def apply_dark_mode_css() -> None:
    """
    Apply dark mode CSS overrides when dark mode is enabled.

    This function injects CSS to transform the light theme into dark theme.
    """
    is_dark = get_theme() == "dark"

    if is_dark:
        st.markdown("""
        <style>
            /* Main background */
            .stApp {
                background-color: #0E1117 !important;
            }

            /* Sidebar */
            section[data-testid="stSidebar"] {
                background-color: #262730 !important;
            }

            /* Main content area */
            .main .block-container {
                background-color: #0E1117 !important;
            }

            /* Text colors */
            .stMarkdown, .stText, p, span, label {
                color: #FAFAFA !important;
            }

            /* Headers */
            h1, h2, h3, h4, h5, h6 {
                color: #FAFAFA !important;
            }

            /* Metric cards */
            [data-testid="stMetric"] {
                background-color: #262730 !important;
                border-color: #3a3d4a !important;
            }

            [data-testid="stMetric"] label {
                color: #a3a8b8 !important;
            }

            [data-testid="stMetric"] [data-testid="stMetricValue"] {
                color: #FAFAFA !important;
            }

            /* Dataframes */
            .stDataFrame {
                background-color: #262730 !important;
            }

            .stDataFrame th {
                background-color: #1a1c24 !important;
                color: #FAFAFA !important;
            }

            .stDataFrame td {
                background-color: #262730 !important;
                color: #FAFAFA !important;
            }

            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                background-color: #262730 !important;
            }

            .stTabs [data-baseweb="tab"] {
                color: #a3a8b8 !important;
            }

            .stTabs [aria-selected="true"] {
                color: #FAFAFA !important;
                background-color: #0E1117 !important;
            }

            /* Input widgets */
            .stSelectbox, .stMultiSelect, .stDateInput {
                background-color: #262730 !important;
            }

            div[data-baseweb="select"] > div {
                background-color: #262730 !important;
                color: #FAFAFA !important;
            }

            /* Buttons */
            .stButton button {
                background-color: #262730 !important;
                color: #FAFAFA !important;
                border-color: #3a3d4a !important;
            }

            .stButton button:hover {
                background-color: #3a3d4a !important;
            }

            /* Expander */
            .streamlit-expanderHeader {
                background-color: #262730 !important;
                color: #FAFAFA !important;
            }

            /* Dividers */
            hr {
                border-color: #3a3d4a !important;
            }

            /* Alerts/Warnings */
            .stAlert {
                background-color: #262730 !important;
                color: #FAFAFA !important;
            }

            /* Info boxes */
            .element-container .stAlert[data-basename="info"] {
                background-color: #1a2a3a !important;
            }
        </style>
        """, unsafe_allow_html=True)


def apply_custom_css() -> None:
    """
    Apply custom CSS based on current theme.

    This is the main entry point for theme CSS application.
    """
    apply_dark_mode_css()

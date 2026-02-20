"""
U1: Theme Manager - Dark mode support for dashboard.

Simplified version using config.toml for theme settings.
Only detects theme and provides color palette for charts.
"""

import streamlit as st
from typing import Literal, Dict

ThemeMode = Literal["light", "dark"]

# Color palettes for charts (config.toml doesn't support runtime chart colors)
CHART_COLORS: Dict[str, Dict[str, str]] = {
    "light": {
        "chart_template": "plotly_white",
        "primary": "#1f77b4",
        "secondary": "#ff7f0e",
        "accent": "#FF4B4B",
    },
    "dark": {
        "chart_template": "plotly_dark",
        "primary": "#1f77b4",
        "secondary": "#ff7f0e",
        "accent": "#FF4B4B",
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

    Uses st.context.theme.base if available (Streamlit 1.40+),
    otherwise falls back to session_state.

    Returns:
        "dark" if dark mode is enabled, "light" otherwise.
    """
    # First check session_state (user toggle)
    if st.session_state.get("dark_mode", False):
        return "dark"

    # Try to detect from Streamlit context
    try:
        if st.context.theme.base == "dark":
            return "dark"
    except AttributeError:
        pass

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
        "Dark Mode",
        value=st.session_state.get("dark_mode", False),
        key="dark_mode_toggle",
        help="Switch between light and dark theme"
    )
    st.session_state.dark_mode = dark_mode
    return dark_mode


def apply_custom_css() -> None:
    """
    Apply minimal custom CSS only for styles not supported by config.toml.

    Most styling is now handled by .streamlit/config.toml.
    This function only adds styles that config.toml cannot configure.
    """
    is_dark = get_theme() == "dark"

    # Only apply minimal CSS for unsupported elements
    if is_dark:
        st.markdown("""
        <style>
            /* Dark mode DataFrame fixes (config.toml doesn't fully support) */
            .stDataFrame th {
                background-color: #262730 !important;
            }
        </style>
        """, unsafe_allow_html=True)

"""
U8: Responsive Layout Utilities - Mobile optimization.

Provides responsive layout utilities for adapting the dashboard
to different screen sizes (desktop, tablet, mobile).
"""

import streamlit as st
from typing import List


def get_responsive_columns(count: int = 4) -> List[st.delta_generator.DeltaGenerator]:
    """
    Get columns with responsive CSS applied.

    Creates the specified number of columns. CSS media queries
    handle responsive behavior (stacking on mobile).

    Args:
        count: Number of columns to create (default: 4).

    Returns:
        List of column DeltaGenerator objects.

    Note:
        Responsive behavior is handled by CSS in apply_responsive_css().
        On mobile (<768px), columns will stack vertically.
    """
    cols = st.columns(count)
    return cols


def apply_responsive_css() -> None:
    """
    Apply responsive CSS for mobile optimization.

    Injects CSS that:
    - Stacks KPI cards vertically on mobile
    - Increases touch targets for mobile interaction
    - Adjusts font sizes for better mobile readability
    - Handles tablet-specific layout adjustments

    Should be called once during app initialization.
    """
    st.markdown("""
    <style>
        /* Mobile responsive adjustments */
        @media (max-width: 768px) {
            /* Stack KPI cards and columns vertically */
            div[data-testid="stHorizontalBlock"] > div {
                flex-direction: column !important;
                width: 100% !important;
            }

            /* Increase touch targets for buttons */
            .stButton button {
                min-height: 44px;
                padding: 12px 20px;
            }

            /* Adjust font sizes for mobile */
            .stMetric label {
                font-size: 0.9rem !important;
            }
            .stMetric [data-testid="stMetricValue"] {
                font-size: 1.2rem !important;
            }

            /* Adjust sidebar width on mobile */
            [data-testid="stSidebar"] {
                width: 280px !important;
            }

            /* Make dataframes scrollable on mobile */
            .stDataFrame {
                overflow-x: auto;
            }

            /* Adjust tabs for mobile */
            .stTabs [role="tab"] {
                padding: 8px 12px;
                font-size: 0.85rem;
            }
        }

        /* Tablet adjustments */
        @media (min-width: 768px) and (max-width: 1024px) {
            /* Allow wrapping for medium screens */
            div[data-testid="stHorizontalBlock"] > div {
                flex-wrap: wrap;
            }

            /* 2-column layout for KPI cards on tablet */
            div[data-testid="stHorizontalBlock"] > div:nth-child(-n+4) {
                width: 50% !important;
            }
        }

        /* Desktop optimizations */
        @media (min-width: 1024px) {
            /* Ensure full utilization of wide layout */
            .block-container {
                max-width: 100%;
                padding-left: 3rem;
                padding-right: 3rem;
            }
        }

        /* Chart container responsiveness */
        .js-plotly-plot {
            width: 100% !important;
        }

        /* Improve data table scrolling */
        .stDataFrame [data-testid="stHorizontalBlock"] {
            overflow-x: auto;
        }
    </style>
    """, unsafe_allow_html=True)

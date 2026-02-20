"""
U2: KPI Dashboard Cards - Key Performance Indicators display.

Displays key metrics at the top of the dashboard:
- Total production quantity
- Production batch count
- Daily average production
- Top produced product
"""

import streamlit as st
import pandas as pd
from datetime import date
from typing import Dict, Any, Optional


def calculate_kpis(
    df: pd.DataFrame,
    date_from: Optional[date],
    date_to: Optional[date]
) -> Dict[str, Any]:
    """
    Calculate KPI metrics from dataframe.

    Args:
        df: Production records dataframe with columns:
            - good_quantity: Production quantity
            - item_code: Product code
            - item_name: Product name
        date_from: Start date of the period
        date_to: End date of the period

    Returns:
        Dict with keys:
            - total_qty: Total production quantity
            - batch_count: Number of production batches
            - daily_avg: Average daily production
            - top_item: Product code with highest production
            - top_item_name: Product name of top item
    """
    if df.empty:
        return {
            "total_qty": 0,
            "batch_count": 0,
            "daily_avg": 0.0,
            "top_item": "-",
            "top_item_name": "-",
        }

    # Calculate total quantity (handle NaN values)
    total_qty = int(df["good_quantity"].fillna(0).sum())
    batch_count = len(df)

    # Calculate daily average
    if date_from and date_to:
        days = (date_to - date_from).days + 1
        daily_avg = total_qty / max(days, 1)
    else:
        # Default: assume 30 days if no date range specified
        daily_avg = total_qty / 30

    # Find top product
    item_totals = df.groupby("item_code")["good_quantity"].sum()
    if not item_totals.empty:
        top_item = str(item_totals.idxmax())
        # Get the name for the top item
        top_item_rows = df[df["item_code"] == top_item]["item_name"]
        if not top_item_rows.empty:
            top_item_name = str(top_item_rows.iloc[0])
        else:
            top_item_name = "-"
    else:
        top_item = "-"
        top_item_name = "-"

    return {
        "total_qty": total_qty,
        "batch_count": batch_count,
        "daily_avg": daily_avg,
        "top_item": top_item,
        "top_item_name": top_item_name,
    }


def render_kpi_cards(kpis: Dict[str, Any], colors: Dict[str, str]) -> None:
    """
    Render 4 KPI metric cards in a row.

    Displays metrics in a horizontal row of 4 cards:
    1. Total production quantity
    2. Production batch count
    3. Daily average production
    4. Top produced product

    Args:
        kpis: KPI values dict from calculate_kpis()
        colors: Theme color palette (not directly used, but available
                for custom styling if needed)
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Production",
            value=f"{kpis['total_qty']:,} ea",
            delta=None
        )

    with col2:
        st.metric(
            label="Batch Count",
            value=f"{kpis['batch_count']:,} batches",
            delta=None
        )

    with col3:
        st.metric(
            label="Daily Average",
            value=f"{kpis['daily_avg']:,.0f} ea",
            delta=None
        )

    with col4:
        # Truncate long product names for display
        top_name = kpis['top_item_name']
        if len(top_name) > 20:
            top_name = top_name[:20] + "..."

        st.metric(
            label="Top Product",
            value=kpis['top_item'],
            delta=top_name if top_name != "-" else None
        )

    st.divider()

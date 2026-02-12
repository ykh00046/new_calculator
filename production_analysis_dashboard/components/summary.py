#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI components for displaying summary metrics.
"""

import streamlit as st
import pandas as pd
from utils.helpers import format_large_number
from utils.data_utils import calculate_daily_stats
from utils.date_utils import calculate_change_percentage


def display_metrics(
    current_data: pd.DataFrame,
    last_data: pd.DataFrame | None = None,
    show_comparison: bool = True,
    display_unit: str = "kg",
):
    """Display KPI metrics for the current period, with optional comparison."""
    # Current stats
    current_total = current_data['good_quantity'].sum()
    current_stats = calculate_daily_stats(current_data)
    current_avg = current_stats['avg']
    current_records = len(current_data)
    current_products = current_data['item_name'].nunique()

    if show_comparison and last_data is not None and not last_data.empty:
        last_total = last_data['good_quantity'].sum()
        last_stats = calculate_daily_stats(last_data)
        last_avg = last_stats['avg']

        total_change = calculate_change_percentage(current_total, last_total)
        avg_change = calculate_change_percentage(current_avg, last_avg)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="총 생산량",
                value=format_large_number(current_total, f" {display_unit}"),
                delta=f"{total_change:.1f}%",
                help=f"비교 기간: {format_large_number(last_total, f' {display_unit}')}"
            )

        with col2:
            st.metric(
                label="평균 일일 생산량",
                value=format_large_number(current_avg, f" {display_unit}/day"),
                delta=f"{avg_change:.1f}%",
                help=f"비교 기간: {format_large_number(last_avg, f' {display_unit}/day')}"
            )

        with col3:
            st.metric(label="기록 수", value=f"{current_records:,}", help="현재 기간의 생산 기록 수")

        with col4:
            st.metric(label="고유 제품 수", value=f"{current_products}", help="현재 기간의 고유 제품 개수")

    else:
        max_daily = current_stats['max']
        min_daily = current_stats['min']

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("총 생산량", format_large_number(current_total, f" {display_unit}"))
        col2.metric("평균 일일", format_large_number(current_avg, f" {display_unit}/day"))
        col3.metric("최대(일별)", format_large_number(max_daily, f" {display_unit}"))
        col4.metric("최소(일별)", format_large_number(min_daily, f" {display_unit}"))


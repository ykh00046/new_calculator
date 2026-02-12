#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd


def display_kpi_ribbon(data: pd.DataFrame, comparison_data: pd.DataFrame = None, comparison_label: str = None):
    """Display key KPIs with optional comparison deltas."""
    if data.empty:
        return

    total_production = data['good_quantity'].sum()
    num_days = (data['production_date'].max() - data['production_date'].min()).days + 1
    daily_avg = total_production / num_days if num_days > 0 else 0
    num_products = data['item_name'].nunique()
    num_records = len(data)

    delta_total = None
    delta_avg = None
    if comparison_data is not None and not comparison_data.empty:
        comp_total = comparison_data['good_quantity'].sum()
        comp_days = (comparison_data['production_date'].max() - comparison_data['production_date'].min()).days + 1
        comp_avg = comp_total / comp_days if comp_days > 0 else 0
        if comp_total > 0:
            delta_total = f"{(total_production - comp_total) / comp_total:.2%}"
        if comp_avg > 0:
            delta_avg = f"{(daily_avg - comp_avg) / comp_avg:.2%}"

    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 생산량", f"{total_production:,.2f}", delta=delta_total, help=f"비교 기간: {comparison_label}" if comparison_label else None)
        with col2:
            st.metric("평균(일별)", f"{daily_avg:,.2f}", delta=delta_avg, help=f"비교 기간: {comparison_label}" if comparison_label else None)
        with col3:
            st.metric("제품 종류", f"{num_products}")
        with col4:
            st.metric("레코드 수", f"{num_records:,}")


#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Weekly analysis tab component
"""

import streamlit as st
import pandas as pd
import logging
from utils.data_utils import calculate_daily_stats
from components.charts import create_product_specific_trend_chart, create_daily_production_chart
from components.summary import display_metrics
from components.product_cards import display_single_product_card

logger = logging.getLogger(__name__)


def display_weekly_tab(
    current_week_data: pd.DataFrame,
    last_week_data: pd.DataFrame,
    product_filter_mode: str,
    selected_products: list,
    display_unit: str,
    cumulative: bool,
    moving_average: str,
):
    """Displays the weekly analysis tab using pre-filtered data."""
    # Header
    if not current_week_data.empty:
        current_start = current_week_data['production_date'].min().date()
        current_end = current_week_data['production_date'].max().date()
        st.subheader(f"주간 분석: {current_start} ~ {current_end}")
        if not last_week_data.empty:
            last_start = last_week_data['production_date'].min().date()
            last_end = last_week_data['production_date'].max().date()
            st.caption(f"비교 기간: 지난주 ({last_start} ~ {last_end})")
    else:
        st.subheader("주간 분석")

    if current_week_data.empty:
        st.warning("해당 주의 데이터가 없습니다.")
        return

    # Metrics
    with st.container(border=True):
        display_metrics(current_week_data, last_week_data, show_comparison=True, display_unit=display_unit)

    # Last week average for reference line
    last_stats = calculate_daily_stats(last_week_data)
    last_avg = last_stats['avg']

    # Daily production chart
    with st.container(border=True):
        create_daily_production_chart(
            current_week_data,
            last_week_avg=last_avg,
            title="일별 생산량",
            display_unit=display_unit,
            cumulative=cumulative,
            moving_average=moving_average,
            chart_key="weekly_daily_chart",
        )
        # 대안 드릴다운: 날짜 선택 위젯
        min_d = current_week_data['production_date'].min().date()
        max_d = current_week_data['production_date'].max().date()
        chosen = st.date_input("상세 보기 날짜 선택", value=max_d, min_value=min_d, max_value=max_d, key="weekly_drill_picker")
        if st.button("상세 보기", key="weekly_drill_btn"):
            st.session_state.drill_down_date = chosen

    # Drill down dialog
    if 'drill_down_date' in st.session_state and st.session_state.drill_down_date:
        @st.dialog(f"상세 내역: {st.session_state.drill_down_date.strftime('%Y-%m-%d')}")
        def show_drill_down():
            date_to_show = st.session_state.drill_down_date
            st.write(f"**{date_to_show.strftime('%Y-%m-%d')} 생산 기록**")

            day_data = current_week_data[current_week_data['production_date'].dt.date == date_to_show]

            if day_data.empty:
                st.write("해당 날짜의 상세 기록이 없습니다.")
            else:
                st.dataframe(day_data[['item_name', 'lot_number', 'good_quantity']], width='stretch')

            if st.button("닫기"):
                st.session_state.drill_down_date = None
                st.rerun()

        show_drill_down()

    # Single product card
    with st.container(border=True):
        st.subheader("개별 제품 현황")
        available_products = sorted(current_week_data['item_name'].unique())
        if available_products:
            selected_single_product = st.selectbox(
                "제품을 선택하세요",
                options=available_products,
                key="weekly_single_product_select",
            )
            if selected_single_product:
                single_product_current_data = current_week_data[current_week_data['item_name'] == selected_single_product]
                single_product_last_data = last_week_data[last_week_data['item_name'] == selected_single_product]
                display_single_product_card(
                    single_product_current_data,
                    single_product_last_data,
                    key_prefix="weekly_single",
                    display_unit=display_unit,
                )
        else:
            st.info("선택된 제품이 없습니다.")

    # Product-specific trend chart
    with st.container(border=True):
        create_product_specific_trend_chart(
            current_week_data,
            product_filter_mode,
            selected_products,
            display_unit=display_unit,
            chart_key="weekly_product_trend",
        )

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Monthly analysis tab component
"""

import streamlit as st
import pandas as pd
import logging
from components.charts import create_product_specific_trend_chart, create_daily_production_chart
from components.summary import display_metrics

logger = logging.getLogger(__name__)


def display_monthly_tab(
    current_month_data: pd.DataFrame,
    last_month_data: pd.DataFrame,
    product_filter_mode: str,
    selected_products: list,
    display_unit: str,
    cumulative: bool,
    moving_average: str,
):
    """Displays the monthly analysis tab using pre-filtered data."""
    if current_month_data.empty:
        st.info("해당 기간의 데이터가 없습니다.")
        return

    start_date = current_month_data['production_date'].min().strftime('%Y-%m-%d')
    end_date = current_month_data['production_date'].max().strftime('%Y-%m-%d')
    st.subheader(f"월간 분석: {start_date} ~ {end_date}")

    with st.container(border=True):
        display_metrics(current_month_data, last_month_data, show_comparison=True, display_unit=display_unit)

    with st.container(border=True):
        create_daily_production_chart(
            current_month_data,
            title="일별 생산량 추이",
            display_unit=display_unit,
            cumulative=cumulative,
            moving_average=moving_average,
            chart_key="monthly_daily_chart",
        )
        # 대안 드릴다운: 날짜 선택 위젯
        min_d = current_month_data['production_date'].min().date()
        max_d = current_month_data['production_date'].max().date()
        chosen = st.date_input("상세 보기 날짜 선택", value=max_d, min_value=min_d, max_value=max_d, key="monthly_drill_picker")
        if st.button("상세 보기", key="monthly_drill_btn"):
            st.session_state.drill_down_date_monthly = chosen

    if 'drill_down_date_monthly' in st.session_state and st.session_state.drill_down_date_monthly:
        @st.dialog(f"상세 내역: {st.session_state.drill_down_date_monthly.strftime('%Y-%m-%d')}")
        def show_monthly_drill_down():
            date_to_show = st.session_state.drill_down_date_monthly
            st.write(f"**{date_to_show.strftime('%Y-%m-%d')} 생산 기록**")

            day_data = current_month_data[current_month_data['production_date'].dt.date == date_to_show]

            if day_data.empty:
                st.write("해당 날짜의 상세 기록이 없습니다.")
            else:
                st.dataframe(day_data[['item_name', 'lot_number', 'good_quantity']], width='stretch')

            if st.button("닫기"):
                st.session_state.drill_down_date_monthly = None
                st.rerun()

        show_monthly_drill_down()

    with st.container(border=True):
        create_product_specific_trend_chart(
            current_month_data,
            product_filter_mode,
            selected_products,
            display_unit=display_unit,
            chart_key="monthly_product_trend",
        )

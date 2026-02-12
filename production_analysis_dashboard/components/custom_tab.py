#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Custom date range analysis tab component
"""

import streamlit as st
import pandas as pd
import logging
from components.charts import create_product_specific_trend_chart, create_daily_production_chart
from components.summary import display_metrics

logger = logging.getLogger(__name__)


def display_custom_tab(
    custom_range_data: pd.DataFrame,
    product_filter_mode: str,
    selected_products: list,
    display_unit: str,
    cumulative: bool,
    moving_average: str,
):
    """Displays the custom date range analysis tab using pre-filtered data."""
    st.subheader("커스텀 기간 분석")

    if custom_range_data.empty:
        st.info("선택한 기간에 데이터가 없습니다. 사이드바에서 기간을 설정해주세요.")
        return

    start_date_str = custom_range_data['production_date'].min().strftime('%Y-%m-%d')
    end_date_str = custom_range_data['production_date'].max().strftime('%Y-%m-%d')
    days = (custom_range_data['production_date'].max() - custom_range_data['production_date'].min()).days + 1
    st.caption(f"분석 기간: {start_date_str} ~ {end_date_str} ({days}일)")

    with st.container(border=True):
        display_metrics(custom_range_data, show_comparison=False, display_unit=display_unit)

    with st.container(border=True):
        create_daily_production_chart(
            custom_range_data,
            title="일별 생산량",
            display_unit=display_unit,
            cumulative=cumulative,
            moving_average=moving_average,
            chart_key="custom_daily_chart",
        )
        # 대안 드릴다운: 날짜 선택 위젯
        min_d = custom_range_data['production_date'].min().date()
        max_d = custom_range_data['production_date'].max().date()
        chosen = st.date_input("상세 보기 날짜 선택", value=max_d, min_value=min_d, max_value=max_d, key="custom_drill_picker")
        if st.button("상세 보기", key="custom_drill_btn"):
            st.session_state.drill_down_date_custom = chosen

    if 'drill_down_date_custom' in st.session_state and st.session_state.drill_down_date_custom:
        @st.dialog(f"상세 내역: {st.session_state.drill_down_date_custom.strftime('%Y-%m-%d')}")
        def show_custom_drill_down():
            date_to_show = st.session_state.drill_down_date_custom
            st.write(f"**{date_to_show.strftime('%Y-%m-%d')} 생산 기록**")

            day_data = custom_range_data[custom_range_data['production_date'].dt.date == date_to_show]

            if day_data.empty:
                st.write("해당 날짜의 상세 기록이 없습니다.")
            else:
                st.dataframe(day_data[['item_name', 'lot_number', 'good_quantity']], width='stretch')

            if st.button("닫기"):
                st.session_state.drill_down_date_custom = None
                st.rerun()

        show_custom_drill_down()

    with st.container(border=True):
        create_product_specific_trend_chart(
            custom_range_data,
            product_filter_mode,
            selected_products,
            display_unit=display_unit,
            chart_key="custom_product_trend",
        )

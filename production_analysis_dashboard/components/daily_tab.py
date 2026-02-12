#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Daily monitoring tab component.
"""

import pandas as pd
import streamlit as st

from components.charts import create_hourly_chart, create_product_specific_trend_chart, create_daily_production_chart
from components.summary import display_metrics
from components.product_cards import display_product_cards, aggregate_product_daily
from utils.data_utils import aggregate_hourly_production, aggregate_daily_production
from utils.date_utils import calculate_change_percentage
from utils.helpers import format_large_number


def display_daily_tab(
    today_data: pd.DataFrame,
    yesterday_data: pd.DataFrame,
    recent_data: pd.DataFrame,
    product_filter_mode: str,
    selected_products: list,
    display_unit: str,
    cumulative: bool,
    moving_average: str,
    target_date=None,
):
    """Displays the daily monitoring tab using pre-filtered data."""
    st.subheader("일간 모니터링")
    if target_date:
        st.caption(f"기준 일자: {target_date}")

    if today_data.empty and recent_data.empty:
        st.info("선택한 날짜에 데이터가 없습니다.")
        return

    # KPI
    with st.container(border=True):
        display_metrics(today_data, yesterday_data, show_comparison=True, display_unit=display_unit)

    # Hourly chart
    with st.container(border=True):
        hourly_today = aggregate_hourly_production(today_data)
        # 시간 정보가 없으면 건너뜀
        if hourly_today['quantity'].sum() == 0:
            st.info("시간 정보가 없는 데이터입니다. 시간대별 차트를 생략합니다.")
        else:
            hourly_yesterday = aggregate_hourly_production(yesterday_data)
            prev_avg = hourly_yesterday['quantity'].mean() if not hourly_yesterday.empty else None
            create_hourly_chart(
                hourly_today,
                prev_avg,
                title="시간대별 생산량 (오늘)",
                display_unit=display_unit,
                chart_key="hourly_today_chart",
            )

    # Recent daily trend (last 14 days by default, within recent_data)
    with st.container(border=True):
        st.subheader("최근 일별 추이")
        if recent_data.empty:
            st.info("최근 기간 데이터가 없습니다.")
        else:
            recent_daily = aggregate_daily_production(recent_data)
            last_week_avg = None
            create_daily_production_chart(
                recent_data,
                last_week_avg=last_week_avg,
                title="일별 생산량 (최근)",
                display_unit=display_unit,
                cumulative=cumulative,
                moving_average=moving_average,
                chart_key="recent_daily_chart",
            )

    # Product cards (today, top N)
    with st.container(border=True):
        st.subheader("오늘 기준 상위 제품")
        total_products = today_data['item_name'].nunique()
        if total_products <= 1:
            max_cards = max(total_products, 1)
            st.caption("표시할 제품 수가 1개 이하입니다.")
        else:
            default_cards = min(10, total_products)
            max_cards = st.slider(
                "표시할 제품 카드 개수 (상위 기준)",
                min_value=1,
                max_value=total_products,
                value=default_cards,
                key="daily_product_cards_limit",
                help="많은 제품을 한 번에 그리면 느려질 수 있습니다.",
            )
        product_daily = aggregate_product_daily(today_data)
        display_product_cards(
            today_data,
            yesterday_data,
            key_prefix="daily_top",
            display_unit=display_unit,
            product_daily=product_daily,
            max_cards=max_cards,
        )

    # Product trend (recent data, top/custom)
    with st.container(border=True):
        create_product_specific_trend_chart(
            recent_data if not recent_data.empty else today_data,
            product_filter_mode,
            selected_products,
            display_unit=display_unit,
            chart_key="daily_product_trend",
        )

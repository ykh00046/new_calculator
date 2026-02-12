#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Product analysis cards and comparison components (clean implementation).
"""

import time
import logging
import pandas as pd
import altair as alt
import streamlit as st

from utils.helpers import format_large_number
from utils.date_utils import calculate_change_percentage

logger = logging.getLogger(__name__)


def _daily_aggregate(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=['date', 'quantity'])
    daily = df.groupby(df['production_date'].dt.date)['good_quantity'].sum().reset_index()
    daily.columns = ['date', 'quantity']
    return daily


@st.cache_data(show_spinner=False)
def aggregate_product_daily(data: pd.DataFrame) -> pd.DataFrame:
    """Pre-aggregate per-product daily sums for reuse across cards/plots."""
    if data.empty:
        return pd.DataFrame(columns=['date', 'product', 'quantity'])
    grouped = (
        data.groupby([data['production_date'].dt.date, 'item_name'])['good_quantity']
        .sum()
        .reset_index()
    )
    grouped.columns = ['date', 'product', 'quantity']
    return grouped


def display_product_cards(
    current_data: pd.DataFrame,
    last_data: pd.DataFrame,
    key_prefix: str = "",
    display_unit: str = "kg",
    product_daily: pd.DataFrame | None = None,
    max_cards: int | None = None,
):
    """Render product summary cards for the current period (simple grid)."""
    start_overall = time.time()

    if current_data.empty:
        st.info("해당 기간에 데이터가 없습니다.")
        return

    daily_all = product_daily if product_daily is not None else aggregate_product_daily(current_data)

    product_totals_current = (
        current_data.groupby('item_name')['good_quantity'].sum().sort_values(ascending=False)
    )
    product_totals_last = (
        last_data.groupby('item_name')['good_quantity'].sum() if last_data is not None and not last_data.empty else pd.Series(dtype=float)
    )

    st.markdown("### 제품별 생산 현황")

    products_list = list(product_totals_current.items())
    total_count = len(products_list)
    if max_cards:
        products_list = products_list[:max_cards]
    total_production = product_totals_current.sum()

    num_cols = 3
    for i in range(0, len(products_list), num_cols):
        cols = st.columns(num_cols)
        for j in range(num_cols):
            idx = i + j
            if idx >= len(products_list):
                continue
            product_name, current_qty = products_list[idx]
            with cols[j]:
                with st.container(border=True):
                    st.markdown(f"**{product_name}**")
                    st.metric(
                        label="생산량",
                        value=format_large_number(current_qty, f" {display_unit}"),
                        delta=None,
                        label_visibility="collapsed",
                    )
                    percentage = (current_qty / total_production * 100) if total_production > 0 else 0
                    st.caption(f"비중: {percentage:.1f}%")

                    if not product_totals_last.empty and product_name in product_totals_last.index:
                        last_qty = float(product_totals_last[product_name])
                        change = calculate_change_percentage(current_qty, last_qty)
                        sign = "▲" if change > 0 else ("▼" if change < 0 else "■")
                        st.caption(f"{sign} {abs(change):.1f}% vs 비교기간")
                    else:
                        st.caption("비교 데이터 없음")

                    with st.expander("일별 추이"):
                        display_product_trend(
                            current_data,
                            product_name,
                            display_unit=display_unit,
                            product_daily=daily_all,
                        )

    if max_cards and total_count > max_cards:
        st.caption(f"상위 {max_cards}개 제품만 표시 중 (총 {total_count}개). 슬라이더로 개수를 조정하세요.")

    st.markdown("---")
    logger.info(f"[제품카드] 총 처리 시간: {time.time() - start_overall:.3f}s")


def display_product_trend(
    data: pd.DataFrame,
    product_name: str,
    display_unit: str = "kg",
    product_daily: pd.DataFrame | None = None,
):
    """Mini line chart for a given product."""
    if product_daily is not None and not product_daily.empty:
        product_data = product_daily[product_daily['product'] == product_name].copy()
        product_data.rename(columns={'product': 'item_name'}, inplace=True)
        product_data['production_date'] = pd.to_datetime(product_data['date'])
        product_data['good_quantity'] = product_data['quantity']
    else:
        product_data = data[data['item_name'] == product_name]

    if product_data.empty:
        st.info("데이터 없음")
        return

    daily_data = (
        product_data[['production_date', 'good_quantity']]
        if product_daily is not None and not product_daily.empty
        else _daily_aggregate(product_data)
    )
    if 'date' not in daily_data.columns:
        daily_data = _daily_aggregate(product_data)

    daily_data['day_of_week'] = pd.to_datetime(daily_data['date']).dt.dayofweek
    korean_days = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
    daily_data['korean_day'] = daily_data['day_of_week'].map(korean_days)

    chart = alt.Chart(daily_data).mark_line(point=True, color='#4A90E2').encode(
        x=alt.X('date:T', title='날짜', axis=alt.Axis(format='%m/%d', labelAngle=-45)),
        y=alt.Y('quantity:Q', title=f'생산량({display_unit})'),
        tooltip=[
            alt.Tooltip('date:T', title='날짜', format='%Y-%m-%d'),
            alt.Tooltip('korean_day:N', title='요일'),
            alt.Tooltip('quantity:Q', title='생산량', format=',.0f'),
        ],
    ).properties(height=200)

    st.altair_chart(chart, width='stretch')

    col1, col2, col3 = st.columns(3)
    col1.metric("평균", format_large_number(daily_data['quantity'].mean(), f" {display_unit}"))
    col2.metric("최대", format_large_number(daily_data['quantity'].max(), f" {display_unit}"))
    col3.metric("최소", format_large_number(daily_data['quantity'].min(), f" {display_unit}"))


def display_product_comparison(current_data: pd.DataFrame, selected_products: list[str], display_unit: str = "kg"):
    """Multi-line comparison for selected products over time."""
    if not selected_products:
        st.info("비교할 제품을 선택하세요.")
        return

    filtered = current_data[current_data['item_name'].isin(selected_products)]
    if filtered.empty:
        st.warning("선택된 제품에 대한 데이터가 없습니다.")
        return

    product_daily = aggregate_product_daily(filtered)

    chart = alt.Chart(product_daily).mark_line(point=True).encode(
        x=alt.X('date:T', title='날짜'),
        y=alt.Y('quantity:Q', title=f'생산량({display_unit})'),
        color=alt.Color('product:N', title='제품', legend=alt.Legend(orient='right')),
        tooltip=[
            alt.Tooltip('date:T', title='날짜', format='%Y-%m-%d'),
            alt.Tooltip('product:N', title='제품'),
            alt.Tooltip('quantity:Q', title='생산량', format=',.0f'),
        ],
    ).properties(height=320).interactive()

    st.altair_chart(chart, width='stretch')


def display_single_product_card(
    current_data: pd.DataFrame,
    last_data: pd.DataFrame = pd.DataFrame(),
    key_prefix: str = "",
    display_unit: str = "kg",
):
    """Compact card for a single product selected by user."""
    if current_data.empty:
        st.info("선택된 제품의 데이터가 없습니다.")
        return

    product_name = current_data['item_name'].iloc[0]
    total_current = current_data['good_quantity'].sum()
    avg_current = current_data.groupby(current_data['production_date'].dt.date)['good_quantity'].sum().mean()

    delta_text = None
    if last_data is not None and not last_data.empty:
        total_last = last_data['good_quantity'].sum()
        change = calculate_change_percentage(total_current, total_last)
        sign = "▲" if change > 0 else ("▼" if change < 0 else "■")
        delta_text = f"{sign} {abs(change):.1f}% vs 비교기간"

    with st.container(border=True):
        st.markdown(f"**{product_name}**")
        col1, col2 = st.columns(2)
        col1.metric("총 생산량", format_large_number(total_current, f" {display_unit}"), delta=delta_text)
        col2.metric("평균(일별)", format_large_number(avg_current, f" {display_unit}/day"))

        with st.expander("일별 추이"):
            display_product_trend(current_data, product_name, display_unit)

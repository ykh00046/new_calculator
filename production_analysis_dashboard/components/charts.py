#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI components for displaying charts (Altair).
"""

import streamlit as st
import pandas as pd
import altair as alt
from typing import List, Optional
from utils.data_utils import aggregate_daily_production
from utils.helpers import format_large_number, CATEGORY_KR_MAP


def create_production_trend_chart(df: pd.DataFrame, selected_categories: List[str], chart_key: str | None = None):
    """Create multi-line production trend chart by category."""
    if df.empty:
        st.info("표시할 데이터가 없습니다.")
        return

    if len(selected_categories) == 1:
        title = f"생산 추세 - {selected_categories[0]}"
    elif len(selected_categories) > 1:
        title = "생산 추세 - 카테고리 비교"
    else:
        title = "생산 추세"

    st.subheader(title)

    daily_summary = df.groupby([
        df['production_date'].dt.date,
        'product_category'
    ])['good_quantity'].sum().reset_index()
    daily_summary.rename(columns={'production_date': 'date'}, inplace=True)
    # Add Korean display label for legend
    daily_summary['category_label'] = daily_summary['product_category'].map(CATEGORY_KR_MAP).fillna(daily_summary['product_category'])

    color_scale = alt.Scale(
        domain=['잉크', '용수', '약품', '기타'],
        range=['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728']
    )

    chart = alt.Chart(daily_summary).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X('date:T', title='날짜', axis=alt.Axis(format='%Y-%m-%d')),
        y=alt.Y('good_quantity:Q', title='생산량 (kg/L)'),
        color=alt.Color('category_label:N', title='카테고리', scale=color_scale,
                        legend=alt.Legend(orient='right', title='카테고리')),
        tooltip=[
            alt.Tooltip('date:T', title='날짜', format='%Y-%m-%d'),
            alt.Tooltip('product_category:N', title='카테고리'),
            alt.Tooltip('good_quantity:Q', title='생산량', format=',.2f')
        ]
    ).properties(height=400).interactive()

    st.altair_chart(chart, width='stretch', key=chart_key)

    with st.expander("요약 통계 보기"):
        summary_stats = daily_summary.groupby('product_category')['good_quantity'].agg([
            ('총합', 'sum'),
            ('평균', 'mean'),
            ('최대(일별)', 'max'),
            ('최소(일별)', 'min')
        ]).round(2)
        st.dataframe(summary_stats, width='stretch')


def create_product_specific_trend_chart(
    data: pd.DataFrame,
    product_filter_mode: str,
    selected_products: List[str],
    display_unit: str = "kg",
    chart_key: str | None = None,
):
    """Create a product-specific trend chart (Top-N/custom)."""
    st.subheader("제품별 생산 추세")

    if product_filter_mode == 'top5':
        top_products = data.groupby('item_name')['good_quantity'].sum().nlargest(5).index.tolist()
        product_data = data[data['item_name'].isin(top_products)]
        st.caption("상위 5개 제품 표시")
    elif product_filter_mode == 'top10':
        top_products = data.groupby('item_name')['good_quantity'].sum().nlargest(10).index.tolist()
        product_data = data[data['item_name'].isin(top_products)]
        st.caption("상위 10개 제품 표시")
    else:
        if selected_products:
            product_data = data[data['item_name'].isin(selected_products)]
            st.caption(f"선택한 {len(selected_products)}개 제품 표시")
        else:
            st.info("제품을 선택하세요.")
            return

    if product_data.empty:
        st.info("선택된 제품의 데이터가 없습니다.")
        return

    product_daily = product_data.groupby([
        product_data['production_date'].dt.date,
        'item_name'
    ])['good_quantity'].sum().reset_index()
    product_daily.columns = ['date', 'product', 'quantity']

    line_chart = alt.Chart(product_daily).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X('date:T', title='날짜'),
        y=alt.Y('quantity:Q', title=f'생산량 ({display_unit})'),
        color=alt.Color('product:N', title='제품', legend=alt.Legend(orient='right')),
        tooltip=[
            alt.Tooltip('date:T', title='날짜', format='%Y-%m-%d'),
            alt.Tooltip('product:N', title='제품'),
            alt.Tooltip('quantity:Q', title=f'생산량 ({display_unit})', format=',.0f')
        ]
    ).properties(height=400).interactive()

    st.altair_chart(line_chart, width='stretch', key=chart_key)

    with st.expander("제품별 요약 통계"):
        product_summary = (
            product_data.groupby('item_name')['good_quantity']
            .agg([('총합', 'sum'), ('평균', 'mean'), ('최대', 'max'), ('최소', 'min')])
            .round(2)
            .sort_values('총합', ascending=False)
        )
        st.dataframe(product_summary, width='stretch')


def create_daily_production_chart(
    data: pd.DataFrame,
    last_week_avg: Optional[float] = None,
    title: str = "일별 생산량",
    display_unit: str = "kg",
    cumulative: bool = False,
    moving_average: str = 'None',
    chart_key: str | None = None,
):
    """Create a daily production bar chart with optional moving average and comparison line."""
    st.subheader(f"**{title}**")

    if data.empty:
        st.info("데이터가 없습니다.")
        return None

    daily_summary = aggregate_daily_production(data)

    if cumulative:
        daily_summary['quantity'] = daily_summary['quantity'].cumsum()
        y_axis_title = f"누적 생산량({display_unit})"
    else:
        y_axis_title = f"일별 생산량({display_unit})"

    daily_summary['day_of_week'] = pd.to_datetime(daily_summary['date']).dt.dayofweek
    korean_days = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
    daily_summary['korean_day'] = daily_summary['day_of_week'].map(korean_days)

    selection = alt.selection_single(encodings=['x'], on='click')

    bars = alt.Chart(daily_summary).mark_bar(color='#4A90E2', size=40).encode(
        x=alt.X('date:T', title='날짜', axis=alt.Axis(format='%m/%d', labelAngle=-45)),
        y=alt.Y('quantity:Q', title=y_axis_title),
        tooltip=[
            alt.Tooltip('date:T', title='날짜', format='%Y-%m-%d'),
            alt.Tooltip('korean_day:N', title='요일'),
            alt.Tooltip('quantity:Q', title=y_axis_title, format=',.0f')
        ],
        color=alt.condition(selection, alt.value('orange'), alt.value('#4A90E2'))
    ).add_params(selection)

    chart_layers = [bars]

    if not cumulative:
        try:
            ma_window = int(str(moving_average).replace('-day', ''))
            if ma_window > 0:
                daily_summary['moving_avg'] = daily_summary['quantity'].rolling(window=ma_window).mean()
                ma_line = alt.Chart(daily_summary.dropna()).mark_line(color='green', size=3).encode(
                    x=alt.X('date:T'),
                    y=alt.Y('moving_avg:Q')
                )
                chart_layers.append(ma_line)
        except (ValueError, AttributeError):
            pass

        if last_week_avg and last_week_avg > 0:
            avg_line = alt.Chart(pd.DataFrame({'y': [last_week_avg]})).mark_rule(
                strokeDash=[5, 5], color='orange', size=2
            ).encode(y='y:Q')
            chart_layers.append(avg_line)

    # Build final chart: use single-view when possible to allow selections in Streamlit
    if len(chart_layers) == 1:
        final_chart = chart_layers[0].properties(height=400)
        selection_mode = "rerun"
    else:
        final_chart = alt.layer(*chart_layers).properties(height=400)
        selection_mode = "ignore"  # selections unsupported for multi-view charts
        st.caption("이동평균 또는 비교선 표시 중에는 선택이 비활성화됩니다.")

    chart_result = st.altair_chart(
        final_chart.interactive(),
        width='stretch',
        on_select=selection_mode,
        key=chart_key,
    )

    if not cumulative and last_week_avg and last_week_avg > 0:
        st.caption(f"점선: 지난주 평균 ({format_large_number(last_week_avg, f' {display_unit}/day')})")

    return chart_result


def create_hourly_chart(
    hourly_df: pd.DataFrame,
    prev_avg: float | None = None,
    title: str = "시간대별 생산량",
    display_unit: str = "kg",
    chart_key: str | None = None,
):
    """시간대별 막대 + 전일/최근 평균선."""
    st.subheader(title)
    if hourly_df.empty:
        st.info("해당 시간대 데이터가 없습니다.")
        return

    bars = alt.Chart(hourly_df).mark_bar(color="#4A90E2").encode(
        x=alt.X('hour:O', title='시각(0-23)', sort='ascending'),
        y=alt.Y('quantity:Q', title=f'생산량({display_unit})'),
        tooltip=[
            alt.Tooltip('hour:O', title='시각'),
            alt.Tooltip('quantity:Q', title='생산량', format=',.0f')
        ]
    )

    layers = [bars]
    if prev_avg is not None and prev_avg > 0:
        avg_line = alt.Chart(pd.DataFrame({'y': [prev_avg]})).mark_rule(
            strokeDash=[5, 5], color='orange', size=2
        ).encode(y='y:Q')
        layers.append(avg_line)
        st.caption(f"기준선: 비교 평균 {format_large_number(prev_avg, f' {display_unit}/h')}")

    final_chart = alt.layer(*layers).properties(height=300)
    st.altair_chart(final_chart.interactive(), width='stretch', key=chart_key)

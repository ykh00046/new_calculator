#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Production Analysis Dashboard (clean)
"""

import os
import logging
from datetime import datetime

import pandas as pd
import streamlit as st

from config import user_settings
from data_access import db_connector
from utils.date_utils import (
    get_current_week_range,
    get_last_week_range,
    get_current_month_range,
    get_last_month_range,
)
from components import weekly_tab, monthly_tab, custom_tab, product_status_tab, daily_tab, kpi_ribbon
from utils.helpers import to_korean_category, to_english_category, resolve_display_unit


# --- Page Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
st.set_page_config(page_title="Production Analysis Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Cache helper ---
def clear_all_caches():
    """Clear Streamlit cache so DB 갱신이 바로 반영되도록 함."""
    try:
        st.cache_data.clear()
    except Exception:
        pass


# --- Session State Initialization ---
def initialize_session_state():
    defaults = {
        'db_path': user_settings.load_db_path(),
        'selected_categories': [],
        'date_range_preset': 'Last 30 Days',
        'start_date': datetime.now() - pd.Timedelta(days=30),
        'end_date': datetime.now(),
        'product_filter_mode': 'top5',
        'selected_products': [],
        'display_unit_mode': 'auto',
        'cumulative_view': False,
        'moving_average': 'None',
        'comparison_period': 'None',
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# --- DB Setup UI ---
def show_db_setup():
    st.title("Database Setup")
    st.warning("데이터베이스 파일(production_analysis.db)의 경로를 지정하세요.")

    uploaded_file = st.file_uploader("DB 파일 선택", type=["db", "sqlite", "sqlite3"])
    if uploaded_file is not None:
        temp_dir = "temp_db"
        os.makedirs(temp_dir, exist_ok=True)
        db_path = os.path.join(temp_dir, uploaded_file.name)
        with open(db_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"데이터베이스 파일이 업로드되었습니다: `{db_path}`")
        clear_all_caches()
        user_settings.save_db_path(db_path)
        st.session_state.db_path = db_path
        st.rerun()

    st.info("또는, 전체 경로를 직접 입력하세요.")
    path_input = st.text_input("전체 경로 입력", "")
    if st.button("경로 적용"):
        if os.path.exists(path_input):
            clear_all_caches()
            user_settings.save_db_path(path_input)
            st.session_state.db_path = path_input
            st.success("데이터베이스 경로가 설정되었습니다!")
            st.rerun()
        else:
            st.error("입력한 경로를 찾을 수 없습니다. 경로를 다시 확인해주세요.")


# --- Sidebar (Korean labels) ---
def setup_sidebar_v2(available_categories, available_products):
    with st.sidebar:
        st.title("필터")
        st.markdown("---")

        # Date range preset
        st.subheader("기간 선택")
        date_preset = st.selectbox(
            "기간 프리셋",
            options=['Last 7 Days', 'Last 30 Days', 'This Month', 'Last Month', 'Custom'],
            key='date_range_preset'
        )

        today = datetime.now()
        if date_preset == 'Last 7 Days':
            st.session_state.start_date, st.session_state.end_date = today - pd.Timedelta(days=7), today
        elif date_preset == 'Last 30 Days':
            st.session_state.start_date, st.session_state.end_date = today - pd.Timedelta(days=30), today
        elif date_preset == 'This Month':
            start_m, end_m = get_current_month_range()
            st.session_state.start_date, st.session_state.end_date = pd.to_datetime(start_m), pd.to_datetime(end_m)
        elif date_preset == 'Last Month':
            start_lm, end_lm = get_last_month_range()
            st.session_state.start_date, st.session_state.end_date = pd.to_datetime(start_lm), pd.to_datetime(end_lm)

        if date_preset == 'Custom':
            st.session_state.start_date = st.date_input("시작일", st.session_state.start_date)
            st.session_state.end_date = st.date_input("종료일", st.session_state.end_date)

        st.markdown("---")

        # Category selection (display in Korean, store English internally)
        st.subheader("카테고리 선택")
        kr_options = to_korean_category(available_categories)
        default_kr = to_korean_category(st.session_state.selected_categories)
        selected_kr = st.multiselect("분석 카테고리", options=kr_options, default=default_kr)
        st.session_state.selected_categories = to_english_category(selected_kr)

        st.markdown("---")

        # Product filters
        st.subheader("제품 상세 필터")
        st.radio("제품 필터 방식", options=['top5', 'top10', 'custom'], key='product_filter_mode', horizontal=True)
        if st.session_state.product_filter_mode == 'custom':
            st.session_state.selected_products = st.multiselect(
                "표시할 제품 선택",
                options=available_products,
                default=st.session_state.selected_products
            )

        st.selectbox("단위", options=['auto', 'kg', 'L'], key='display_unit_mode', help="카테고리에 따라 단위를 자동 조정하거나 수동 선택합니다.")
        st.toggle("누적 보기", key='cumulative_view', help="차트의 값을 누적으로 표시합니다.")
        st.selectbox("이동 평균", options=['None', '7-day', '14-day', '30-day'], key='moving_average', help="추세선에 이동 평균을 적용합니다.")
        st.selectbox("비교 기간", options=['None', 'Previous Period', 'Previous Year'], key='comparison_period', help="현재 기간과 다른 기간을 비교합니다.")

        st.markdown("---")

        if st.button("필터 적용", type="primary"):
            st.rerun()
        if st.button("데이터 새로고침", help="캐시를 삭제하고 DB를 다시 읽어옵니다."):
            clear_all_caches()
            st.rerun()
        if st.button("DB 변경"):
            clear_all_caches()
            st.session_state.db_path = None
            user_settings.save_db_path("")
            st.rerun()


# --- Main Application ---
def main_app(db_path: str):
    @st.cache_data(ttl=3600)
    def get_available_categories_cached(_db_path, _db_mtime):
        return db_connector.get_available_categories(_db_path, _db_mtime)

    @st.cache_data(ttl=3600)
    def load_production_data(_db_path, start_date, end_date, categories, _db_mtime):
        return db_connector.get_production_data(_db_path, start_date, end_date, categories, _db_mtime)

    st.title("생산 분석 대시보드")

    with st.spinner("초기 데이터 로드 중..."):
        temp_start_date = datetime.now() - pd.Timedelta(days=365 * 2)
        temp_end_date = datetime.now()
        db_mtime = os.path.getmtime(db_path) if os.path.exists(db_path) else None
        available_cats = get_available_categories_cached(db_path, db_mtime)
        all_data_for_filters = load_production_data(
            db_path,
            temp_start_date.strftime('%Y-%m-%d'),
            temp_end_date.strftime('%Y-%m-%d'),
            available_cats,
            db_mtime,
        )

    available_products = (
        sorted(all_data_for_filters['item_name'].unique()) if not all_data_for_filters.empty else []
    )

    setup_sidebar_v2(available_cats, available_products)

    if not st.session_state.selected_categories:
        st.info("왼쪽 사이드바에서 하나 이상의 분석 카테고리를 선택하세요.")
        st.stop()

    start_date = pd.to_datetime(st.session_state.start_date).date()
    end_date = pd.to_datetime(st.session_state.end_date).date()

    main_data = all_data_for_filters[
        (all_data_for_filters['production_date'].dt.date >= start_date)
        & (all_data_for_filters['production_date'].dt.date <= end_date)
        & (all_data_for_filters['product_category'].isin(st.session_state.selected_categories))
    ]

    # Comparison period
    comparison_data = pd.DataFrame()
    comparison_label = None
    period_delta = (end_date - start_date)
    if st.session_state.comparison_period == 'Previous Period':
        comp_start_date = start_date - period_delta - pd.Timedelta(days=1)
        comp_end_date = end_date - period_delta - pd.Timedelta(days=1)
        comparison_label = f"{comp_start_date.strftime('%Y-%m-%d')} ~ {comp_end_date.strftime('%Y-%m-%d')}"
    elif st.session_state.comparison_period == 'Previous Year':
        comp_start_date = start_date.replace(year=start_date.year - 1)
        comp_end_date = end_date.replace(year=end_date.year - 1)
        comparison_label = "전년 동기"
    if comparison_label:
        comparison_data = all_data_for_filters[
            (all_data_for_filters['production_date'].dt.date >= comp_start_date)
            & (all_data_for_filters['production_date'].dt.date <= comp_end_date)
            & (all_data_for_filters['product_category'].isin(st.session_state.selected_categories))
        ]

    if main_data.empty:
        st.warning("선택한 기간/카테고리에 데이터가 없습니다.")
        st.stop()

    # Display unit (handles mixed category selection)
    display_unit, is_mixed_unit = resolve_display_unit(
        st.session_state.selected_categories,
        st.session_state.display_unit_mode,
    )
    if is_mixed_unit:
        st.info("용수(Water)와 다른 카테고리를 함께 선택했습니다. 차트 축은 kg/L(혼합)로 표시됩니다.")

    # KPI ribbon
    try:
        kpi_ribbon.display_kpi_ribbon(main_data, comparison_data, comparison_label)
    except Exception:
        pass

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["일간", "주간", "월간", "커스텀", "제품 현황"])

    cumulative_view = st.session_state.cumulative_view
    moving_average = st.session_state.moving_average

    with tab1:
        # Daily tab: today/yesterday/recent 30 days slice for performance
        today = datetime.now().date()
        target_date = today
        if main_data.empty:
            today_data = pd.DataFrame()
            yesterday_data = pd.DataFrame()
            recent_data = pd.DataFrame()
        else:
            today_data = main_data[main_data['production_date'].dt.date == target_date]
            if today_data.empty:
                target_date = main_data['production_date'].max().date()
                today_data = main_data[main_data['production_date'].dt.date == target_date]
            yesterday = target_date - pd.Timedelta(days=1)
            recent_start = target_date - pd.Timedelta(days=30)
            yesterday_data = main_data[main_data['production_date'].dt.date == yesterday]
            recent_data = main_data[main_data['production_date'].dt.date >= recent_start]

        daily_tab.display_daily_tab(
            today_data,
            yesterday_data,
            recent_data,
            st.session_state.product_filter_mode,
            st.session_state.selected_products,
            display_unit,
            cumulative_view,
            moving_average,
            target_date=target_date,
        )

    with tab2:
        c_start, c_end = get_current_week_range()
        l_start, l_end = get_last_week_range()
        current_week_data = main_data[(main_data['production_date'].dt.date >= c_start) & (main_data['production_date'].dt.date <= c_end)]
        last_week_data = main_data[(main_data['production_date'].dt.date >= l_start) & (main_data['production_date'].dt.date <= l_end)]
        weekly_tab.display_weekly_tab(current_week_data, last_week_data, st.session_state.product_filter_mode, st.session_state.selected_products, display_unit, cumulative_view, moving_average)

    with tab3:
        c_start, c_end = get_current_month_range()
        l_start, l_end = get_last_month_range()
        current_month_data = main_data[(main_data['production_date'].dt.date >= c_start) & (main_data['production_date'].dt.date <= c_end)]
        last_month_data = main_data[(main_data['production_date'].dt.date >= l_start) & (main_data['production_date'].dt.date <= l_end)]
        monthly_tab.display_monthly_tab(current_month_data, last_month_data, st.session_state.product_filter_mode, st.session_state.selected_products, display_unit, cumulative_view, moving_average)

    with tab4:
        custom_tab.display_custom_tab(main_data, st.session_state.product_filter_mode, st.session_state.selected_products, display_unit, cumulative_view, moving_average)

    with tab5:
        product_status_tab.display_product_status_tab(main_data, display_unit)


# --- Entry Point ---
if __name__ == "__main__":
    initialize_session_state()
    if not st.session_state.db_path or not os.path.exists(st.session_state.db_path):
        show_db_setup()
    else:
        main_app(st.session_state.db_path)

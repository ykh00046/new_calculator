#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Product Status Tab component (clean version)
"""

import time
import logging
import pandas as pd
import streamlit as st

from components.product_cards import (
    display_product_cards,
    display_product_comparison,
    aggregate_product_daily,
)

logger = logging.getLogger(__name__)


def display_product_status_tab(product_status_data: pd.DataFrame, display_unit: str):
    """Displays the product status tab using pre-filtered data."""
    st.subheader("제품 현황 분석")

    if product_status_data.empty:
        st.warning("선택한 기간/카테고리에 데이터가 없습니다.")
        return

    # Pre-aggregate per-product daily sums to reuse in cards/comparison (performance)
    product_daily = aggregate_product_daily(product_status_data)

    # Product cards
    start_time = time.time()
    with st.container(border=True):
        total_products = product_status_data['item_name'].nunique()
        if total_products <= 1:
            max_cards = max(total_products, 1)
            st.caption("표시할 제품 수가 1개 이하입니다.")
        else:
            default_cards = min(12, total_products)
            max_cards = st.slider(
                "표시할 제품 카드 개수 (상위 기준)",
                min_value=1,
                max_value=total_products,
                value=default_cards,
                key="product_cards_limit",
                help="많은 제품을 한 번에 그리면 느려질 수 있습니다.",
            )
        display_product_cards(
            product_status_data,
            pd.DataFrame(),
            key_prefix="product_status",
            display_unit=display_unit,
            product_daily=product_daily,
            max_cards=max_cards,
        )
    logger.info(f"[제품현황] 카드 렌더링: {time.time() - start_time:.3f}s")

    st.empty()

    # Product comparison
    start_time = time.time()
    with st.container(border=True):
        st.markdown("### 여러 제품 비교")

        available_products = sorted(product_status_data['item_name'].unique())
        if len(available_products) == 0:
            st.info("비교할 제품이 없습니다.")
        else:
            selected_compare_products = st.multiselect(
                "비교할 제품을 선택하세요 (최대 10개)",
                options=available_products,
                default=available_products[:3] if len(available_products) >= 3 else available_products,
                max_selections=10,
                key="product_status_compare",
            )

            if selected_compare_products:
                display_product_comparison(
                    product_status_data,
                    selected_compare_products,
                    display_unit=display_unit,
                )
            else:
                st.info("오른쪽 상단에서 제품을 선택하세요.")

    logger.info(f"[제품현황] 비교 렌더링: {time.time() - start_time:.3f}s")

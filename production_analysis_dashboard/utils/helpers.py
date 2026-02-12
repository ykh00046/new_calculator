#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions for the dashboard.
"""

import pandas as pd


def format_large_number(num, suffix=''):
    """Formats a large number into a human-readable format (K, M)."""
    if pd.isna(num):
        return f"0{suffix}"
    num = float(num)

    if abs(num) < 1000:
        return f"{num:,.0f}{suffix}"
    elif abs(num) < 1_000_000:
        return f"{num/1000:,.1f}K{suffix}"
    else:
        return f"{num/1_000_000:,.1f}M{suffix}"


# Category label mapping (internal -> display)
CATEGORY_KR_MAP = {
    'Ink': '잉크',
    'Water': '용수',
    'Chemical': '약품',
    'Other': '기타',
}

CATEGORY_EN_MAP = {v: k for k, v in CATEGORY_KR_MAP.items()}
# Legacy label support (이전 한글 라벨 대응)
LEGACY_KR_TO_EN = {
    '수': 'Water',
    '화학': 'Chemical',
    '잉크': 'Ink',
    '기타': 'Other',
}


def to_korean_category(labels):
    """Map English category label(s) to Korean display label(s)."""
    if isinstance(labels, list):
        return [CATEGORY_KR_MAP.get(x, x) for x in labels]
    return CATEGORY_KR_MAP.get(labels, labels)


def to_english_category(labels):
    """Map Korean display category label(s) to English internal label(s)."""
    if isinstance(labels, list):
        return [CATEGORY_EN_MAP.get(x, LEGACY_KR_TO_EN.get(x, x)) for x in labels]
    return CATEGORY_EN_MAP.get(labels, LEGACY_KR_TO_EN.get(labels, labels))


def resolve_display_unit(selected_categories, display_unit_mode: str):
    """
    Decide which display unit label to use based on categories and mode.

    Returns:
        tuple[str, bool]: (unit_label, is_mixed)
    """
    if display_unit_mode != 'auto':
        return display_unit_mode, False

    if not selected_categories:
        return 'kg', False

    unique = set(selected_categories)
    if 'Water' in unique and len(unique) > 1:
        # Mixed units (Water uses L, others kg) -> show combined label to avoid misinterpretation
        return 'kg/L', True
    if unique == {'Water'}:
        return 'L', False

    return 'kg', False

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data access module for connecting to the SQLite database.
Provides cached queries and robust parsing for dates/quantities.
"""

import sqlite3
import pandas as pd
import logging
import streamlit as st

logger = logging.getLogger(__name__)


def _categorize_product(item_code: str) -> str:
    """Return canonical English category based on item_code (case-insensitive).

    Categories: 'Ink' | 'Water' | 'Chemical' | 'Other'
    """
    if not isinstance(item_code, str):
        return 'Unknown'

    code_upper = item_code.upper()
    if code_upper.startswith('BC'):
        return 'Ink'
    if code_upper.startswith('BW'):
        return 'Water'
    if code_upper.startswith('B') and len(code_upper) > 1 and code_upper[1].isdigit():
        return 'Chemical'
    return 'Other'


@st.cache_data(show_spinner=False, ttl=300)
def get_available_categories(db_path: str, db_mtime: float | None = None) -> list[str]:
    """Get list of available product categories from the database."""
    # db_mtime is included only to help cache busting when DB is replaced
    try:
        con = sqlite3.connect(db_path)
        # Decode legacy CP949 bytes to avoid mojibake in item names
        con.text_factory = (
            lambda b: b.decode('cp949', errors='ignore') if isinstance(b, bytes) else b
        )
        df = pd.read_sql_query("SELECT DISTINCT item_code FROM production_records", con)
        con.close()

        categories = df['item_code'].apply(_categorize_product).unique()
        # Keep 'Other' visible so 사용자가 제외할지 선택 가능. Unknown만 숨김.
        return sorted([c for c in categories if c != 'Unknown'])
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        return []


@st.cache_data(show_spinner=False, ttl=300)
def get_production_data(
    db_path: str,
    start_date,
    end_date,
    categories: list[str] | None = None,
    db_mtime: float | None = None,
) -> pd.DataFrame:
    """Query production records for date range and optional categories.

    Note: Categories are English labels as returned by _categorize_product.
    """
    try:
        con = sqlite3.connect(db_path)
        # Decode legacy CP949 bytes to avoid mojibake in text fields
        con.text_factory = (
            lambda b: b.decode('cp949', errors='ignore') if isinstance(b, bytes) else b
        )

        where_clauses = ["production_date BETWEEN ? AND ?"]
        params: list = [start_date, end_date]

        # Only push category filtering to SQL when all categories map to clear patterns.
        # If 'Other' is included, fetch all categories first to avoid dropping data.
        supported_filter_cats = {'Ink', 'Water', 'Chemical'}
        apply_sql_category_filter = bool(categories) and set(categories).issubset(supported_filter_cats)

        if apply_sql_category_filter:
            category_clauses: list[str] = []
            for cat in categories:
                if cat == 'Ink':
                    category_clauses.append("(item_code LIKE 'BC%' OR item_code LIKE 'bc%')")
                elif cat == 'Water':
                    category_clauses.append("(item_code LIKE 'BW%' OR item_code LIKE 'bw%')")
                elif cat == 'Chemical':
                    category_clauses.append("(item_code GLOB 'B[0-9]*' OR item_code GLOB 'b[0-9]*')")
            if category_clauses:
                where_clauses.append(f"({' OR '.join(category_clauses)})")

        query = (
            "SELECT * FROM production_records WHERE " + " AND ".join(where_clauses)
        )
        df = pd.read_sql_query(query, con, params=params)
        con.close()

        if df.empty:
            return df

        # Parse dates
        if 'production_date' in df.columns:
            df['production_date'] = (
                df['production_date']
                .astype(str)
                .str.extract(r'(\d{4}-\d{2}-\d{2})', expand=False)
            )
            df['production_date'] = pd.to_datetime(
                df['production_date'], format='%Y-%m-%d', errors='coerce'
            )
            invalid_dates = df['production_date'].isna().sum()
            if invalid_dates:
                logger.warning(
                    f"Dropped {invalid_dates} rows with invalid production_date while parsing"
                )
            df.dropna(subset=['production_date'], inplace=True)

        # Categorize
        if 'item_code' in df.columns:
            df['product_category'] = df['item_code'].apply(_categorize_product)

        # Coerce quantity
        if 'good_quantity' in df.columns:
            df['good_quantity'] = pd.to_numeric(df['good_quantity'], errors='coerce').fillna(0)

        # Filter by categories (safety)
        if categories:
            df = df[df['product_category'].isin(categories)]

        category_info = f" (categories: {', '.join(categories)})" if categories else ""
        logger.info(
            f"Loaded {len(df)} production records from {start_date} to {end_date}{category_info}"
        )
        return df

    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        st.error(f"데이터 로드 실패: {e}")
        st.stop()
        return pd.DataFrame()

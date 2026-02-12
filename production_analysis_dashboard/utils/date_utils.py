#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Date utility functions for the dashboard.
"""

from datetime import datetime, timedelta
import pandas as pd


def get_current_week_range():
    """
    최근 7일 범위 반환 (오늘 기준 뒤로 6일)

    Returns:
        tuple: (start_date, end_date)
    """
    today = datetime.today().date()
    start_date = today - timedelta(days=6)

    return start_date, today


def get_last_week_range():
    """
    지난 7일 범위 반환 (7~13일 전)

    Returns:
        tuple: (start_date, end_date)
    """
    today = datetime.today().date()
    last_week_end = today - timedelta(days=7)
    last_week_start = today - timedelta(days=13)

    return last_week_start, last_week_end


def get_current_month_range():
    """
    Returns the start and end date of the current calendar month.
    """
    today = datetime.today().date()
    start_date = today.replace(day=1)
    end_date = (start_date + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
    return start_date, end_date.date()


def get_last_month_range():
    """
    Returns the start and end date of the previous calendar month.
    """
    today = datetime.today().date()
    end_of_last_month = (today.replace(day=1) - pd.Timedelta(days=1))
    start_of_last_month = end_of_last_month.replace(day=1)
    return start_of_last_month, end_of_last_month


def get_month_range(days=30):
    """
    최근 N일 범위 반환

    Args:
        days: 일수 (기본 30일)

    Returns:
        tuple: (start_date, end_date)
    """
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=days-1)

    return start_date, end_date


def calculate_week_average(df, date_column='production_date', value_column='good_quantity'):
    """
    주간 일평균 계산

    Args:
        df: DataFrame
        date_column: 날짜 컬럼명
        value_column: 값 컬럼명

    Returns:
        float: 일평균 생산량
    """
    if df.empty:
        return 0.0

    daily_total = df.groupby(df[date_column].dt.date)[value_column].sum()
    return daily_total.mean()


def calculate_change_percentage(current_value, previous_value):
    """
    변화율 계산

    Args:
        current_value: 현재 값
        previous_value: 이전 값

    Returns:
        float: 변화율 (%)
    """
    if previous_value == 0:
        return 0.0 if current_value == 0 else 100.0

    change = ((current_value - previous_value) / previous_value) * 100
    return round(change, 1)

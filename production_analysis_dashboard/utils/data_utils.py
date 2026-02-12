#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data processing utility functions for the dashboard.
"""

import pandas as pd


def aggregate_daily_production(data, date_column='production_date', value_column='good_quantity'):
    """
    일별 생산량 집계 함수

    Args:
        data: DataFrame with production data
        date_column: 날짜 컬럼명 (default: 'production_date')
        value_column: 값 컬럼명 (default: 'good_quantity')

    Returns:
        DataFrame: 'date'와 'quantity' 컬럼을 가진 일별 집계 데이터
    """
    if data.empty:
        return pd.DataFrame(columns=['date', 'quantity'])

    daily_summary = data.groupby(data[date_column].dt.date)[value_column].sum().reset_index()
    daily_summary.columns = ['date', 'quantity']

    return daily_summary


def calculate_daily_stats(data, date_column='production_date', value_column='good_quantity'):
    """
    일별 통계 계산 (평균, 최대, 최소)

    Args:
        data: DataFrame with production data
        date_column: 날짜 컬럼명
        value_column: 값 컬럼명

    Returns:
        dict: {'avg': float, 'max': float, 'min': float}
    """
    if data.empty:
        return {'avg': 0.0, 'max': 0.0, 'min': 0.0}

    daily_totals = data.groupby(data[date_column].dt.date)[value_column].sum()

    return {
        'avg': daily_totals.mean(),
        'max': daily_totals.max(),
        'min': daily_totals.min()
    }


def aggregate_hourly_production(data, date_column='production_date', value_column='good_quantity'):
    """
    시간대별 생산량 집계 (0~23시). 시간 정보 없는 행은 제외.

    Returns:
        DataFrame: columns ['hour', 'quantity']
    """
    if data.empty:
        return pd.DataFrame(columns=['hour', 'quantity'])

    df = data.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

    hourly = (
        df.dropna(subset=[date_column])
        .assign(hour=df[date_column].dt.hour)
        .groupby('hour')[value_column]
        .sum()
        .reindex(range(24), fill_value=0)
        .reset_index()
    )
    hourly.columns = ['hour', 'quantity']
    return hourly

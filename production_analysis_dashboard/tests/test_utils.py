import pandas as pd

from data_access.db_connector import _categorize_product
from utils.data_utils import aggregate_daily_production, calculate_daily_stats
from utils.helpers import resolve_display_unit, to_korean_category


def test_categorize_product():
    assert _categorize_product('BC123') == 'Ink'
    assert _categorize_product('bw-001') == 'Water'
    assert _categorize_product('B5-XYZ') == 'Chemical'
    assert _categorize_product('X123') == 'Other'
    assert _categorize_product(None) == 'Unknown'


def test_aggregate_daily_production_and_stats():
    df = pd.DataFrame({
        'production_date': pd.to_datetime(['2024-11-01', '2024-11-01', '2024-11-02']),
        'good_quantity': [10, 20, 5],
    })

    daily = aggregate_daily_production(df)
    # Expect two dates: 2024-11-01 -> 30, 2024-11-02 -> 5
    assert len(daily) == 2
    assert daily.loc[daily['date'] == pd.Timestamp('2024-11-01').date(), 'quantity'].iloc[0] == 30
    assert daily.loc[daily['date'] == pd.Timestamp('2024-11-02').date(), 'quantity'].iloc[0] == 5

    stats = calculate_daily_stats(df)
    assert stats['avg'] == (30 + 5) / 2
    assert stats['max'] == 30
    assert stats['min'] == 5


def test_resolve_display_unit():
    assert resolve_display_unit(['Water'], 'auto') == ('L', False)
    assert resolve_display_unit(['Water', 'Ink'], 'auto') == ('kg/L', True)
    assert resolve_display_unit(['Ink'], 'auto') == ('kg', False)
    assert resolve_display_unit(['Ink'], 'kg') == ('kg', False)
    # Default when nothing selected should be safe fallback
    unit, mixed = resolve_display_unit([], 'auto')
    assert unit == 'kg' and mixed is False


def test_to_korean_category_includes_other():
    assert to_korean_category(['Other']) == ['기타']

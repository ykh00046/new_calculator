import sqlite3
import pandas as pd

db_path = r'C:\X\material_box\Raw_material_dashboard_v2\data\production_analysis.db'

try:
    con = sqlite3.connect(db_path)

    # Count total records
    count_query = "SELECT COUNT(*) as total FROM production_records"
    total = pd.read_sql_query(count_query, con)
    print(f"Total records: {total['total'].iloc[0]}")

    # Get sample data
    sample_query = "SELECT * FROM production_records LIMIT 10"
    sample = pd.read_sql_query(sample_query, con)
    print("\nSample data:")
    print(sample.to_string())

    # Get date range
    date_query = "SELECT MIN(production_date) as min_date, MAX(production_date) as max_date FROM production_records"
    dates = pd.read_sql_query(date_query, con)
    print(f"\nDate range: {dates['min_date'].iloc[0]} to {dates['max_date'].iloc[0]}")

    # Get unique item codes
    item_query = "SELECT DISTINCT item_code FROM production_records ORDER BY item_code LIMIT 20"
    items = pd.read_sql_query(item_query, con)
    print(f"\nSample item codes ({len(items)}):")
    print(items['item_code'].tolist())

    con.close()
except Exception as e:
    print(f"Error: {e}")

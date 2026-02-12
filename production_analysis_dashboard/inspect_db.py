import sqlite3
import os

db_path = r'C:\X\material_box\Raw_material_dashboard_v2\data\production_analysis.db'

if not os.path.exists(db_path):
    print(f"Error: Database file not found at {db_path}")
else:
    try:
        con = sqlite3.connect(db_path)
        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print("--- Database Schema ---")
        for table_name in tables:
            table_name = table_name[0]
            print(f"\n[Table: {table_name}]")
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns = cursor.fetchall()
            for column in columns:
                print(f"  - {column[1]} ({column[2]})")
        con.close()
    except Exception as e:
        print(f"An error occurred: {e}")

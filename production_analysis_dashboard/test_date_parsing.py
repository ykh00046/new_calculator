import sqlite3
import pandas as pd
try:
    from config import user_settings, settings
    _user_db = user_settings.load_db_path()
    db_path = _user_db if _user_db else str(settings.DATABASE_PATH)
except Exception:
    # Fallback: local project DB name
    db_path = 'production_analysis.db'

try:
    con = sqlite3.connect(db_path)
    con.text_factory = lambda x: x.decode('cp949', errors='ignore') if isinstance(x, bytes) else x

    # Get sample dates
    query = "SELECT production_date FROM production_records LIMIT 20"
    df = pd.read_sql_query(query, con)

    print("=== Original Date Formats ===")
    for idx, date_str in enumerate(df['production_date'].head(20)):
        print(f"{idx+1}. '{date_str}' (type: {type(date_str)})")

    # Test conversion
    print("\n=== After Replacement ===")
    df['converted'] = df['production_date'].str.replace('오전', 'AM', regex=False).str.replace('오후', 'PM', regex=False)
    for idx, date_str in enumerate(df['converted'].head(20)):
        print(f"{idx+1}. '{date_str}'")

    # Test parsing
    print("\n=== Parsing Test ===")
    df['parsed'] = pd.to_datetime(df['converted'], format='%Y-%m-%d %p %I:%M:%S', errors='coerce')
    print(f"Successfully parsed: {df['parsed'].notna().sum()}/{len(df)}")
    print(f"Failed to parse: {df['parsed'].isna().sum()}/{len(df)}")

    if df['parsed'].isna().any():
        print("\nFailed examples:")
        failed = df[df['parsed'].isna()][['production_date', 'converted']].head(5)
        print(failed.to_string())

    con.close()
except Exception as e:
    print(f"Error: {e}")

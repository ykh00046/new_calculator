# config/user_settings.py
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent
DB_PATH_CONFIG_FILE = CONFIG_DIR / 'db_path.conf'

def save_db_path(path: str):
    """Saves the database path to the config file."""
    with open(DB_PATH_CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(path)

def load_db_path() -> str | None:
    """Loads the database path from the config file."""
    if not DB_PATH_CONFIG_FILE.exists():
        return None
    with open(DB_PATH_CONFIG_FILE, 'r', encoding='utf-8') as f:
        path = f.read().strip()
        return path if path else None

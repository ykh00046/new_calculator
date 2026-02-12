# Configuration settings for the dashboard
from pathlib import Path

# The database is expected to be in the project's root directory
# Path to the project root (one level up from the 'config' directory)
ROOT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = ROOT_DIR / 'production_analysis.db'

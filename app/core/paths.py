from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]  # /app
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DB_PATH = BASE_DIR / "wms.db"

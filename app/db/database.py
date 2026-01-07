
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "wms.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

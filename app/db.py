import sqlite3
from contextlib import contextmanager
from .core.paths import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # inventory: current stock by (warehouse, location, item_code, lot, spec)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT NOT NULL,
        location TEXT NOT NULL,
        brand TEXT DEFAULT '',
        item_code TEXT NOT NULL,
        item_name TEXT NOT NULL,
        lot TEXT DEFAULT '',
        spec TEXT DEFAULT '',
        qty INTEGER NOT NULL DEFAULT 0,
        note TEXT DEFAULT '',
        updated_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory
    ON inventory (warehouse, location, item_code, lot, spec)
    """)

    # history: immutable logs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        type TEXT NOT NULL,
        warehouse TEXT DEFAULT '',
        location TEXT DEFAULT '',
        from_location TEXT DEFAULT '',
        to_location TEXT DEFAULT '',
        brand TEXT DEFAULT '',
        item_code TEXT DEFAULT '',
        item_name TEXT DEFAULT '',
        lot TEXT DEFAULT '',
        spec TEXT DEFAULT '',
        qty INTEGER DEFAULT 0,
        note TEXT DEFAULT '',
        operator TEXT DEFAULT ''
    )
    """)

    # calendar memo: one memo per date
    cur.execute("""
    CREATE TABLE IF NOT EXISTS calendar_memo (
        date TEXT PRIMARY KEY, -- YYYY-MM-DD
        memo TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

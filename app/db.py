import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from app.core.paths import DB_PATH

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_column(cur: sqlite3.Cursor, table: str, col: str, coldef: str) -> None:
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coldef}")

def init_db() -> None:
    conn = get_db()
    cur = conn.cursor()

    # inventory
    cur.execute("""CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT NOT NULL,
        location TEXT NOT NULL,
        brand TEXT NOT NULL DEFAULT '',
        item_code TEXT NOT NULL,
        item_name TEXT NOT NULL,
        lot TEXT NOT NULL,
        spec TEXT NOT NULL,
        qty INTEGER NOT NULL,
        note TEXT DEFAULT '',
        updated_at TEXT NOT NULL
    )""")
    # migration for older DBs
    _ensure_column(cur, "inventory", "brand", "TEXT NOT NULL DEFAULT ''")

    cur.execute("""CREATE INDEX IF NOT EXISTS idx_inventory_key
        ON inventory(warehouse, location, brand, item_code, lot, spec)""")

    # history
    cur.execute("""CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL, -- 입고/출고/이동
        warehouse TEXT NOT NULL,
        operator TEXT NOT NULL DEFAULT '',
        brand TEXT NOT NULL DEFAULT '',
        item_code TEXT NOT NULL,
        item_name TEXT NOT NULL,
        lot TEXT NOT NULL,
        spec TEXT NOT NULL,
        from_location TEXT DEFAULT '',
        to_location TEXT DEFAULT '',
        qty INTEGER NOT NULL,
        note TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )""")
    _ensure_column(cur, "history", "brand", "TEXT NOT NULL DEFAULT ''")

    cur.execute("""CREATE INDEX IF NOT EXISTS idx_history_created
        ON history(created_at)""")

    # damage codes (CS/파손 분류 기준)
    cur.execute("""CREATE TABLE IF NOT EXISTS damage_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,      -- 대분류: 물류/사옥/운송/하차지/가공공정/원자재/부상
        type TEXT NOT NULL,          -- 유형: 수작업/지게차/보관/운송 하차/재단 불량 등
        situation

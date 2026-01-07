# app/db.py
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.paths import DB_PATH


# =====================================================
# DB CONNECTION
# =====================================================

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_column(cur: sqlite3.Cursor, table: str, col: str, coldef: str) -> None:
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coldef}")


# =====================================================
# INIT / MIGRATION
# =====================================================

def init_db() -> None:
    conn = get_db()
    cur = conn.cursor()

    # -------------------------------------------------
    # INVENTORY (현재고)
    # -------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
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
        )
    """)
    _ensure_column(cur, "inventory", "brand", "TEXT NOT NULL DEFAULT ''")

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_inventory_key
        ON inventory (warehouse, location, brand, item_code, lot, spec)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_inventory_updated
        ON inventory (updated_at)
    """)

    # -------------------------------------------------
    # HISTORY (입고 / 출고 / 이동)
    # -------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
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
        )
    """)
    _ensure_column(cur, "history", "brand", "TEXT NOT NULL DEFAULT ''")

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_history_created
        ON history (created_at)
    """)

    # -------------------------------------------------
    # DAMAGE CODES (CS / 파손 코드)
    # -------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS damage_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            type TEXT NOT NULL,
            situation TEXT NOT NULL,
            description TEXT DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_damage_codes_key
        ON damage_codes (category, type, situation)
    """)

    # -------------------------------------------------
    # DAMAGE HISTORY (CS / 파손 이력)
    # -------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS damage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_at TEXT NOT NULL,
            warehouse TEXT NOT NULL,
            location TEXT NOT NULL,
            brand TEXT NOT NULL DEFAULT '',
            item_code TEXT NOT NULL,
            item_name TEXT NOT NULL,
            lot TEXT NOT NULL,
            spec TEXT NOT NULL,
            qty INTEGER NOT NULL,
            damage_code_id INTEGER NOT NULL,
            detail TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(damage_code_id) REFERENCES damage_codes(id)
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_damage_history_date
        ON damage_history (occurred_at)
    """)

    # -------------------------------------------------
    # DAMAGE CODE SEED
    # -------------------------------------------------
    cur.execute("SELECT COUNT(*) FROM damage_codes")
    if cur.fetchone()[0] == 0:
        seed_rows = [
            ("물류", "수작업", "이동", "수작업 이동 중 발생"),
            ("물류", "수작업", "낙하", "수작업 중 낙하"),
            ("물류", "지게차", "충격", "지게차 충돌"),
            ("운송", "사고", "충돌", "운송 사고"),
            ("가공공정", "업체", "제품 파손", "가공 중 파손"),
        ]
        cur.executemany("""
            INSERT OR IGNORE INTO damage_codes
            (category, type, situation, description)
            VALUES (?, ?, ?, ?)
        """, seed_rows)

    conn.commit()
    conn.close()


# =====================================================
# INVENTORY
# =====================================================

def upsert_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    qty_delta: int,
    note: str = "",
) -> None:
    """
    ✅ 재고 upsert 정책
    - 동일 key 존재 시:
        * qty / note / updated_at 만 변경
        * ❌ item_name 변경 금지
    - 신규 row 생성 시에만 item_name 저장
    """
    now = datetime.now().isoformat(timespec="seconds")

    warehouse = (warehouse or "").strip()
    location = (location or "").strip()
    brand = (brand or "").strip()
    item_code = (item_code or "").strip()
    item_name = (item_name or "").strip()
    lot = (lot or "").strip()
    spec = (spec or "").strip()
    note = (note or "").strip()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, qty
        FROM inventory
        WHERE warehouse=? AND location=? AND brand=?
          AND item_code=? AND lot=? AND spec=?
    """, (warehouse, location, brand, item_code, lot, spec))

    row = cur.fetchone()

    if row:
        new_qty = max(0, int(row["qty"]) + int(qty_delta))
        cur.execute("""
            UPDATE inventory
            SET qty=?, note=?, updated_at=?
            WHERE id=?
        """, (new_qty, note, now, int(row["id"])))
    else:
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name,
             lot, spec, qty, note, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            warehouse, location, brand,
            item_code, item_name,
            lot, spec,
            max(0, int(qty_delta)),
            note, now
        ))

    conn.commit()
    conn.close()


def query_inventory(
    warehouse: str = "",
    location: str = "",
    brand: str = "",
    item_code: str = "",
    lot: str = "",
    spec: str = "",
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()

    where = []
    params: List[Any] = []

    if warehouse:
        where.append("warehouse=?")
        params.append(warehouse)
    if location:
        where.append("location LIKE ?")
        params.append(f"%{location}%")
    if brand:
        where.append("brand=?")
        params.append(brand)
    if item_code:
        where.append("item_code LIKE ?")
        params.append(f"%{item_code}%")
    if lot:
        where.append("lot LIKE ?")
        params.append(f"%{lot}%")
    if spec:
        where.append("spec LIKE ?")
        params.append(f"%{spec}%")

    sql = "SELECT * FROM inventory"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =====================================================
# HISTORY
# =====================================================

def add_history(
    type: str,
    warehouse: str,
    operator: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    from_location: str = "",
    to_location: str = "",
    qty: int = 0,
    note: str = "",
    dedup_seconds: int = 5,
) -> None:
    now = datetime.now()
    threshold = (now - timedelta(seconds=dedup_seconds)).isoformat(timespec="seconds")
    now_str = now.isoformat(timespec="seconds")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) FROM history
        WHERE type=? AND warehouse=? AND brand=?
          AND item_code=? AND lot=? AND spec=?
          AND from_location=? AND to_location=?
          AND qty=? AND created_at>=?
    """, (
        type, warehouse, brand,
        item_code, lot, spec,
        from_location, to_location,
        int(qty), threshold
    ))

    if cur.fetchone()[0] > 0:
        conn.close()
        return

    cur.execute("""
        INSERT INTO history
        (type, warehouse, operator, brand,
         item_code, item_name, lot, spec,
         from_location, to_location,
         qty, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        type, warehouse, operator, brand,
        item_code, item_name, lot, spec,
        from_location, to_location,
        int(qty), note, now_str
    ))

    conn.commit()
    conn.close()

# app/db.py
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
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


# =====================================================
# INIT / MIGRATION
# =====================================================

def init_db() -> None:
    conn = get_db()
    cur = conn.cursor()

    # -----------------------------
    # INVENTORY (qty: REAL)
    # -----------------------------
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
            qty REAL NOT NULL,
            note TEXT DEFAULT '',
            updated_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_inventory_key
        ON inventory (warehouse, location, brand, item_code, lot, spec)
    """)

    # -----------------------------
    # HISTORY (qty: REAL)
    # -----------------------------
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
            qty REAL NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_history_created
        ON history (created_at)
    """)

    # -----------------------------
    # DAMAGE CODES (CS MASTER)
    # -----------------------------
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

    # -----------------------------
    # DAMAGE HISTORY (CS LOG)
    # -----------------------------
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
            qty REAL NOT NULL,
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

    # -----------------------------
    # DAMAGE CODE SEED (1회)
    # -----------------------------
    cur.execute("SELECT COUNT(*) FROM damage_codes")
    if cur.fetchone()[0] == 0:
        seed_rows = [
            ("물류", "수작업", "이동", "수작업 이동 중 발생"),
            ("물류", "수작업", "낙하", "수작업 중 낙하"),
            ("물류", "지게차", "충격", "지게차 충돌"),
            ("운송", "하차", "부주의", "하차 중 파손"),
            ("가공", "업체", "불량", "가공 불량"),
        ]
        cur.executemany("""
            INSERT INTO damage_codes (category, type, situation, description)
            VALUES (?, ?, ?, ?)
        """, seed_rows)

    conn.commit()
    conn.close()


# =====================================================
# UTIL
# =====================================================

def _q3(val) -> float:
    """소숫점 3자리 고정"""
    return float(
        Decimal(str(val)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)
    )


def _norm(v: Optional[str]) -> str:
    return (v or "").strip()


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
    qty_delta: float,
    note: str = "",
) -> None:
    """
    정책:
    - 동일 key 존재 시: qty / note / updated_at 만 변경
    - item_name은 신규 row에서만 저장
    """
    now = datetime.now().isoformat(timespec="seconds")
    qty_delta = _q3(qty_delta)

    warehouse = _norm(warehouse)
    location = _norm(location)
    brand = _norm(brand)
    item_code = _norm(item_code)
    item_name = _norm(item_name)
    lot = _norm(lot)
    spec = _norm(spec)
    note = _norm(note)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, qty FROM inventory
        WHERE warehouse=? AND location=? AND brand=?
          AND item_code=? AND lot=? AND spec=?
    """, (warehouse, location, brand, item_code, lot, spec))

    row = cur.fetchone()

    if row:
        new_qty = _q3(max(0, float(row["qty"]) + qty_delta))
        cur.execute("""
            UPDATE inventory
            SET qty=?, note=?, updated_at=?
            WHERE id=?
        """, (new_qty, note, now, row["id"]))
    else:
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name,
             lot, spec, qty, note, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            warehouse, location, brand, item_code, item_name,
            lot, spec, max(0, qty_delta), note, now
        ))

    conn.commit()
    conn.close()


def query_history(
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()

    where = []
    params: List[Any] = []

    # created_at 예: 2026-01-08T14:32:10
    if year:
        y = f"{int(year):04d}"
        if month:
            m = f"{int(month):02d}"
            if day:
                d = f"{int(day):02d}"
                where.append("created_at LIKE ?")
                params.append(f"{y}-{m}-{d}%")
            else:
                where.append("created_at LIKE ?")
                params.append(f"{y}-{m}%")
        else:
            where.append("created_at LIKE ?")
            params.append(f"{y}%")

    sql = "SELECT * FROM history"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ?"
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
    from_location: str,
    to_location: str,
    qty: float,
    note: str = "",
    dedup_seconds: int = 5,
) -> None:
    now = datetime.now()
    now_str = now.isoformat(timespec="seconds")
    threshold = (now - timedelta(seconds=dedup_seconds)).isoformat(timespec="seconds")
    qty = _q3(qty)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) FROM history
        WHERE type=? AND warehouse=? AND brand=? AND item_code=?
          AND lot=? AND spec=? AND from_location=? AND to_location=?
          AND ABS(qty - ?) < 0.0005
          AND created_at >= ?
    """, (
        _norm(type), _norm(warehouse), _norm(brand), _norm(item_code),
        _norm(lot), _norm(spec), _norm(from_location), _norm(to_location),
        qty, threshold
    ))

    if cur.fetchone()[0] > 0:
        conn.close()
        return

    cur.execute("""
        INSERT INTO history
        (type, warehouse, operator, brand,
         item_code, item_name, lot, spec,
         from_location, to_location, qty, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        _norm(type), _norm(warehouse), _norm(operator), _norm(brand),
        _norm(item_code), _norm(item_name), _norm(lot), _norm(spec),
        _norm(from_location), _norm(to_location),
        qty, _norm(note), now_str
    ))

    conn.commit()
    conn.close()


def query_history(limit: int = 500) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM history
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =====================================================
# DAMAGE / CS
# =====================================================

def list_damage_codes(
    category: str = "",
    type: str = "",
    situation: str = "",
    active_only: bool = True,
) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()

    where = []
    params = []

    if active_only:
        where.append("is_active=1")
    if category:
        where.append("category=?")
        params.append(_norm(category))
    if type:
        where.append("type=?")
        params.append(_norm(type))
    if situation:
        where.append("situation=?")
        params.append(_norm(situation))

    sql = "SELECT * FROM damage_codes"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY category, type, situation"

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def add_damage_history(
    occurred_at: str,
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    qty: float,
    damage_code_id: int,
    detail: str = "",
    deduct_inventory: bool = False,
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    qty = _q3(qty)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO damage_history
        (occurred_at, warehouse, location, brand,
         item_code, item_name, lot, spec,
         qty, damage_code_id, detail, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        _norm(occurred_at), _norm(warehouse), _norm(location), _norm(brand),
        _norm(item_code), _norm(item_name), _norm(lot), _norm(spec),
        qty, int(damage_code_id), _norm(detail), now
    ))

    conn.commit()
    conn.close()

    if deduct_inventory:
        upsert_inventory(
            warehouse=warehouse,
            location=location,
            brand=brand,
            item_code=item_code,
            item_name=item_name,
            lot=lot,
            spec=spec,
            qty_delta=-qty,
            note="CS 차감",
        )


def query_damage_history(
    year: Optional[int] = None,
    month: Optional[int] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()

    where = []
    params = []

    if year:
        if month:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{year:04d}-{month:02d}%")
        else:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{year:04d}%")

    sql = """
        SELECT dh.*, dc.category, dc.type, dc.situation
        FROM damage_history dh
        JOIN damage_codes dc ON dh.damage_code_id = dc.id
    """
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY dh.occurred_at DESC, dh.id DESC LIMIT ?"
    params.append(limit)

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
def query_damage_summary_by_category(
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()

    where = []
    params = []

    if year:
        if month:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{year:04d}-{month:02d}%")
        else:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{year:04d}%")

    sql = """
        SELECT dc.category, COUNT(*) AS cnt
        FROM damage_history dh
        JOIN damage_codes dc ON dh.damage_code_id = dc.id
    """
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY dc.category ORDER BY cnt DESC"

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

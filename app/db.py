# app/db.py
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from app.core.paths import DB_PATH


# =====================================================
# DB CONNECTION & UTILS
# =====================================================

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _q3(val) -> float:
    if val is None:
        return 0.0
    return float(
        Decimal(str(val)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)
    )


def _norm(v: Optional[str]) -> str:
    return (v or "").strip()


# =====================================================
# INIT / MIGRATION
# =====================================================

def init_db() -> None:
    conn = get_db()
    try:
        cur = conn.cursor()

        # INVENTORY
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

        # HISTORY
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
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON history (created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_key ON history (warehouse, item_code, lot, spec)")

        # DAMAGE CODES
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

        # DAMAGE HISTORY
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
        cur.execute("CREATE INDEX IF NOT EXISTS idx_damage_history_date ON damage_history (occurred_at)")

        # SEED DAMAGE CODES
        cur.execute("SELECT COUNT(*) FROM damage_codes")
        if cur.fetchone()[0] == 0:
            seed_rows = [
                ("물류", "수작업", "이동", "수작업 이동 중 발생"),
                ("물류", "수작업", "낙하", "수작업 중 낙하"),
                ("물류", "지게차", "충격", "지게차 충돌"),
                ("운송", "하차", "부주의", "하차 중 파손"),
                ("가공", "업체", "불량", "가공 불량"),
            ]
            cur.executemany(
                "INSERT INTO damage_codes (category, type, situation, description) VALUES (?, ?, ?, ?)",
                seed_rows
            )

        conn.commit()
    finally:
        conn.close()


# =====================================================
# INVENTORY
# =====================================================

def query_inventory(
    warehouse: Optional[str] = None,
    location: Optional[str] = None,
    item_code: Optional[str] = None,
    brand: Optional[str] = None,
    lot: Optional[str] = None,
    spec: Optional[str] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []

        if warehouse:
            where.append("warehouse=?"); params.append(_norm(warehouse))
        if location:
            where.append("location LIKE ?"); params.append(f"%{_norm(location)}%")
        if item_code:
            where.append("item_code LIKE ?"); params.append(f"%{_norm(item_code)}%")
        if brand:
            where.append("brand=?"); params.append(_norm(brand))
        if lot:
            where.append("lot LIKE ?"); params.append(f"%{_norm(lot)}%")
        if spec:
            where.append("spec LIKE ?"); params.append(f"%{_norm(spec)}%")

        sql = "SELECT * FROM inventory"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


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
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        delta = _q3(qty_delta)

        w, l, b, ic, iname, lt, sp = map(
            _norm, [warehouse, location, brand, item_code, item_name, lot, spec]
        )

        cur.execute("""
            SELECT id, qty FROM inventory
            WHERE warehouse=? AND location=? AND brand=?
              AND item_code=? AND lot=? AND spec=?
        """, (w, l, b, ic, lt, sp))
        row = cur.fetchone()

        if row:
            new_qty = _q3(max(0, float(row["qty"]) + delta))
            cur.execute(
                "UPDATE inventory SET qty=?, note=?, updated_at=? WHERE id=?",
                (new_qty, _norm(note), now, row["id"])
            )
        else:
            cur.execute("""
                INSERT INTO inventory
                (warehouse, location, brand, item_code, item_name,
                 lot, spec, qty, note, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                w, l, b, ic, iname, lt, sp,
                max(0, delta), _norm(note), now
            ))

        conn.commit()
    finally:
        conn.close()


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
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now()
        now_str = now.isoformat(timespec="seconds")
        threshold = (now - timedelta(seconds=dedup_seconds)).isoformat(timespec="seconds")
        q = _q3(qty)

        cur.execute("""
            SELECT COUNT(*) FROM history
            WHERE type=? AND warehouse=? AND item_code=? AND lot=? AND spec=?
              AND from_location=? AND to_location=?
              AND ABS(qty - ?) < 0.0005
              AND created_at >= ?
        """, (
            _norm(type), _norm(warehouse), _norm(item_code),
            _norm(lot), _norm(spec),
            _norm(from_location), _norm(to_location),
            q, threshold
        ))

        if cur.fetchone()[0] > 0:
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
            q, _norm(note), now_str
        ))

        conn.commit()
    finally:
        conn.close()


def query_history(
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []

        if year:
            pattern = f"{year:04d}"
            if month:
                pattern += f"-{month:02d}"
                if day:
                    pattern += f"-{day:02d}"
            where.append("created_at LIKE ?")
            params.append(f"{pattern}%")

        sql = "SELECT * FROM history"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


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
    try:
        cur = conn.cursor()
        where, params = [], []

        if active_only:
            where.append("is_active=1")
        if category:
            where.append("category=?"); params.append(_norm(category))
        if type:
            where.append("type=?"); params.append(_norm(type))
        if situation:
            where.append("situation=?"); params.append(_norm(situation))

        sql = "SELECT * FROM damage_codes"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY category, type, situation"

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


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
    conn = get_db()
    try:
        cur = conn.cursor()
        q = _q3(qty)
        now = datetime.now().isoformat(timespec="seconds")

        cur.execute("""
            INSERT INTO damage_history
            (occurred_at, warehouse, location, brand,
             item_code, item_name, lot, spec,
             qty, damage_code_id, detail, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            _norm(occurred_at), _norm(warehouse), _norm(location), _norm(brand),
            _norm(item_code), _norm(item_name), _norm(lot), _norm(spec),
            q, int(damage_code_id), _norm(detail), now
        ))

        conn.commit()

        if deduct_inventory:
            upsert_inventory(
                warehouse, location, brand,
                item_code, item_name, lot, spec,
                -q, "CS 차감"
            )
    finally:
        conn.close()

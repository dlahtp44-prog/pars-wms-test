# app/db.py
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from app.core.paths import DB_PATH

# =====================================================
# DB CONNECTION (🔥 핵심 수정)
# =====================================================

def get_db() -> sqlite3.Connection:
    """
    SQLite 안전 연결
    - timeout / busy_timeout 필수
    - check_same_thread=False (FastAPI 멀티스레드 대응)
    """
    conn = sqlite3.connect(
        str(DB_PATH),
        timeout=10,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


# =====================================================
# UTILS
# =====================================================

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

        # inventory
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

        # history
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

        # damage codes
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

        # damage history
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

        # seed damage codes
        cur.execute("SELECT COUNT(*) FROM damage_codes")
        if cur.fetchone()[0] == 0:
            cur.executemany("""
            INSERT INTO damage_codes (category, type, situation, description)
            VALUES (?, ?, ?, ?)
            """, [
                ("물류", "수작업", "이동", "수작업 이동 중"),
                ("물류", "수작업", "낙하", "수작업 낙하"),
                ("물류", "지게차", "충격", "지게차 충돌"),
                ("운송", "하차", "부주의", "하차 중 파손"),
                ("가공", "업체", "불량", "가공 불량"),
            ])

        conn.commit()
    finally:
        conn.close()


# =====================================================
# INVENTORY (공통 내부 함수)
# =====================================================

def _upsert_inventory_with_conn(
    conn: sqlite3.Connection,
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    qty_delta: float,
    note: str = "",
) -> bool:
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    delta = _q3(qty_delta)

    w, l, b, ic, iname, lt, sp = map(
        _norm, [warehouse, location, brand, item_code, item_name, lot, spec]
    )

    cur.execute("""
        SELECT id, qty FROM inventory
        WHERE warehouse=? AND location=? AND brand=? AND item_code=? AND lot=? AND spec=?
    """, (w, l, b, ic, lt, sp))
    row = cur.fetchone()

    if row:
        current = float(row["qty"])
        if delta < 0 and current < abs(delta):
            return False
        new_qty = _q3(current + delta)
        if new_qty <= 0:
            cur.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
        else:
            cur.execute("""
                UPDATE inventory
                SET qty=?, note=?, updated_at=?
                WHERE id=?
            """, (new_qty, _norm(note), now, row["id"]))
    else:
        if delta <= 0:
            return False
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name, lot, spec, qty, note, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (w, l, b, ic, iname, lt, sp, delta, _norm(note), now))

    return True


def upsert_inventory(**kwargs) -> bool:
    conn = get_db()
    try:
        ok = _upsert_inventory_with_conn(conn, **kwargs)
        if ok:
            conn.commit()
        return ok
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
):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO history
        (type, warehouse, operator, brand, item_code, item_name,
         lot, spec, from_location, to_location, qty, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            _norm(type), _norm(warehouse), _norm(operator), _norm(brand),
            _norm(item_code), _norm(item_name), _norm(lot), _norm(spec),
            _norm(from_location), _norm(to_location),
            _q3(qty), _norm(note),
            datetime.now().isoformat(timespec="seconds"),
        ))
        conn.commit()
    finally:
        conn.close()


# =====================================================
# DAMAGE / CS (🔥 완전 수정)
# =====================================================

def list_damage_codes(active_only: bool = True) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM damage_codes"
        if active_only:
            sql += " WHERE is_active=1"
        sql += " ORDER BY category, type, situation"
        cur.execute(sql)
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
):
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        q = _q3(qty)

        # 🔒 하나의 트랜잭션
        cur.execute("""
        INSERT INTO damage_history (
            occurred_at, warehouse, location, brand,
            item_code, item_name, lot, spec,
            qty, damage_code_id, detail, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            _norm(occurred_at), _norm(warehouse), _norm(location), _norm(brand),
            _norm(item_code), _norm(item_name), _norm(lot), _norm(spec),
            q, int(damage_code_id), _norm(detail), now
        ))

        if deduct_inventory:
            ok = _upsert_inventory_with_conn(
                conn,
                warehouse=warehouse,
                location=location,
                brand=brand,
                item_code=item_code,
                item_name=item_name,
                lot=lot,
                spec=spec,
                qty_delta=-q,
                note="CS 차감",
            )
            if not ok:
                raise ValueError("재고 부족")

        conn.commit()
    finally:
        conn.close()

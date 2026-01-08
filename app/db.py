# app/db.py
import sqlite3
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from app.core.paths import DB_PATH

# =====================================================
# DB CONNECTION
# =====================================================

def get_db() -> sqlite3.Connection:
    """
    SQLite 안전 연결
    - FastAPI 멀티스레드 대응
    - database is locked 방지
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

def _norm(v: Optional[str]) -> str:
    return (v or "").strip()


def _q3(v) -> float:
    if v is None:
        return 0.0
    return float(
        Decimal(str(v)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)
    )


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
            updated_at TEXT NOT NULL
        )
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_inventory_key
        ON inventory (warehouse, location, brand, item_code, lot, spec)
        """)

        # HISTORY (입고/출고/이동)
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

        # DAMAGE HISTORY (CS)
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

        # SEED DAMAGE CODES
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
# INVENTORY CORE (단일 코어)
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
                SET qty=?, updated_at=?
                WHERE id=?
            """, (new_qty, now, row["id"]))
    else:
        if delta <= 0:
            return False
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name, lot, spec, qty, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (w, l, b, ic, iname, lt, sp, delta, now))

    return True


# =====================================================
# INVENTORY PUBLIC ENTRY (🔥 중요)
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
) -> bool:
    """
    엑셀 입고 / 출고 / 이동 / CS
    모든 재고 증감의 단일 진입점
    """
    conn = get_db()
    try:
        ok = _upsert_inventory_with_conn(
            conn,
            warehouse=warehouse,
            location=location,
            brand=brand,
            item_code=item_code,
            item_name=item_name,
            lot=lot,
            spec=spec,
            qty_delta=qty_delta,
        )
        if ok:
            conn.commit()
        return ok
    finally:
        conn.close()


# =====================================================
# INVENTORY QUERY
# =====================================================

def query_inventory(
    warehouse: Optional[str] = None,
    location: Optional[str] = None,
    brand: Optional[str] = None,
    item_code: Optional[str] = None,
    lot: Optional[str] = None,
    spec: Optional[str] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = ["qty > 0"], []

        if warehouse:
            where.append("warehouse=?"); params.append(_norm(warehouse))
        if location:
            where.append("location LIKE ?"); params.append(f"%{_norm(location)}%")
        if brand:
            where.append("brand=?"); params.append(_norm(brand))
        if item_code:
            where.append("item_code LIKE ?"); params.append(f"%{_norm(item_code)}%")
        if lot:
            where.append("lot LIKE ?"); params.append(f"%{_norm(lot)}%")
        if spec:
            where.append("spec LIKE ?"); params.append(f"%{_norm(spec)}%")

        sql = "SELECT * FROM inventory WHERE " + " AND ".join(where)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(int(limit))

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# =====================================================
# HISTORY WRITE
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
# HISTORY QUERY (통합 화면용)
# =====================================================

def query_all_history(
    year: Optional[int] = None,
    month: Optional[int] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []

        if year:
            pat = f"{int(year):04d}"
            if month:
                pat += f"-{int(month):02d}"
            where.append("created_at LIKE ?")
            params.append(f"{pat}%")

        sql = f"""
        SELECT * FROM (
            SELECT
                created_at,
                type,
                warehouse,
                brand,
                item_code,
                item_name,
                lot,
                spec,
                from_location AS location,
                qty,
                note
            FROM history

            UNION ALL

            SELECT
                created_at,
                'CS' AS type,
                warehouse,
                brand,
                item_code,
                item_name,
                lot,
                spec,
                location,
                qty * -1 AS qty,
                detail AS note
            FROM damage_history
        )
        """

        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

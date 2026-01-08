# app/db.py
import sqlite3
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from app.core.paths import DB_PATH


# =====================================================
# DB CONNECTION
# =====================================================

def get_db(immediate: bool = False) -> sqlite3.Connection:
    """
    SQLite 안전 연결
    - immediate=True: 쓰기 작업 시 'database is locked' 방지를 위해 즉시 배타적 락을 요청
    """
    conn = sqlite3.connect(
        str(DB_PATH),
        timeout=15,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")
    
    if immediate:
        # 쓰기 트랜잭션을 즉시 시작하여 중간에 락이 걸리는 것을 방지
        conn.execute("BEGIN IMMEDIATE")
    return conn


# =====================================================
# UTILS
# =====================================================

def _norm(v: Any) -> str:
    """None이나 공백을 처리하여 깨끗한 문자열 반환"""
    if v is None:
        return ""
    return str(v).strip()


def _q3(v: Any) -> float:
    """소수점 3자리 반올림 (Decimal 활용으로 부동소수점 오차 방지)"""
    if v is None or v == "":
        return 0.0
    try:
        return float(Decimal(str(v)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP))
    except (ValueError, TypeError):
        return 0.0


# =====================================================
# INIT / MIGRATION
# =====================================================

def init_db() -> None:
    conn = get_db(immediate=True)
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

        # SEED DATA
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
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =====================================================
# INVENTORY CORE (트랜잭션 내에서만 호출 권장)
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
# INVENTORY PUBLIC ENTRY
# =====================================================

def upsert_inventory(*args, **kwargs) -> bool:
    if args and kwargs:
        raise TypeError("upsert_inventory는 positional 또는 keyword 중 한 방식만 사용하세요.")

    if args:
        if len(args) != 8:
            raise TypeError(f"필요 인자 8개 (현재 {len(args)}개)")
        warehouse, location, brand, item_code, item_name, lot, spec, qty_delta = args
    else:
        # kwargs.get()이 None을 반환할 경우를 대비해 _norm 처리
        warehouse = _norm(kwargs.get("warehouse"))
        location = _norm(kwargs.get("location"))
        brand = _norm(kwargs.get("brand"))
        item_code = _norm(kwargs.get("item_code"))
        item_name = _norm(kwargs.get("item_name"))
        lot = _norm(kwargs.get("lot"))
        spec = _norm(kwargs.get("spec"))
        qty_delta = kwargs.get("qty_delta") or 0.0

    conn = get_db(immediate=True)
    try:
        ok = _upsert_inventory_with_conn(
            conn,
            warehouse=warehouse, location=location, brand=brand,
            item_code=item_code, item_name=item_name, lot=lot,
            spec=spec, qty_delta=float(qty_delta),
        )
        if ok:
            conn.commit()
        return ok
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =====================================================
# HISTORY WRITE
# =====================================================

def add_history(**kwargs):
    conn = get_db(immediate=True)
    try:
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute("""
        INSERT INTO history
        (type, warehouse, operator, brand, item_code, item_name,
         lot, spec, from_location, to_location, qty, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            _norm(kwargs.get("type")), _norm(kwargs.get("warehouse")), 
            _norm(kwargs.get("operator")), _norm(kwargs.get("brand")),
            _norm(kwargs.get("item_code")), _norm(kwargs.get("item_name")), 
            _norm(kwargs.get("lot")), _norm(kwargs.get("spec")),
            _norm(kwargs.get("from_location")), _norm(kwargs.get("to_location")),
            _q3(kwargs.get("qty")), _norm(kwargs.get("note")), now
        ))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =====================================================
# DAMAGE HISTORY WRITE (CS) - 트랜잭션 강화
# =====================================================

def add_damage_history(
    occurred_at: str, warehouse: str, location: str, brand: str,
    item_code: str, item_name: str, lot: str, spec: str,
    qty: float, damage_code_id: int, detail: str = "",
    deduct_inventory: bool = False,
):
    conn = get_db(immediate=True)
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        q = _q3(qty)

        # 1. 파손 기록 저장
        cur.execute("""
        INSERT INTO damage_history (
            occurred_at, warehouse, location, brand, item_code, item_name,
            lot, spec, qty, damage_code_id, detail, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            _norm(occurred_at), _norm(warehouse), _norm(location), _norm(brand),
            _norm(item_code), _norm(item_name), _norm(lot), _norm(spec),
            q, int(damage_code_id), _norm(detail), now
        ))

        # 2. 재고 차감 처리
        if deduct_inventory:
            ok = _upsert_inventory_with_conn(
                conn, warehouse=warehouse, location=location, brand=brand,
                item_code=item_code, item_name=item_name, lot=lot,
                spec=spec, qty_delta=-q
            )
            if not ok:
                raise ValueError(f"재고 부족: {item_name} (현재 재고가 파손 입력량보다 적습니다.)")

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# 나머지 Query 관련 함수들은 단순 SELECT이므로 get_db() 사용 시 
# immediate=False(기본값)로 유지하여 읽기 성능을 확보하면 됩니다.

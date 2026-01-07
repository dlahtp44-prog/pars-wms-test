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
    # HISTORY (입고 / 출고 / 이동 이력)
    # -------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,              -- 입고 / 출고 / 이동 (또는 inbound/outbound/move)
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
    # DAMAGE CODES (CS / 파손 기준 마스터)
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
    # NOTE: 기본 정책은 재고 자동 차감 안 함 (옵션 처리)
    # -------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS damage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_at TEXT NOT NULL,       -- 발생일 (YYYY-MM-DD)
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
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_damage_history_code
        ON damage_history (damage_code_id)
    """)

    # -------------------------------------------------
    # DAMAGE CODE SEED (최초 1회)
    # -------------------------------------------------
    cur.execute("SELECT COUNT(*) FROM damage_codes")
    if (cur.fetchone() or [0])[0] == 0:
        seed_rows = [
            ("물류", "수작업", "이동", "수작업 이동 중 발생"),
            ("물류", "수작업", "낙하", "수작업 중 낙하"),
            ("물류", "수작업", "충격", "수작업 중 외부 충격"),
            ("물류", "지게차", "이동", "지게차 이동 작업"),
            ("물류", "지게차", "낙하", "지게차 작업 중 낙하"),
            ("물류", "지게차", "충격", "지게차 충돌 / 충격"),
            ("물류", "보관", "적재 기준 미준수", "적재 기준 위반"),
            ("물류", "보관", "장기 적재", "장기 적재로 인한 변형"),

            ("사옥", "수작업", "이동", "사옥 내 수작업 이동"),
            ("사옥", "수작업", "낙하", "사옥 내 수작업 낙하"),
            ("사옥", "수작업", "충격", "사옥 내 충격"),

            ("운송", "하차", "부주의", "운송 중 부주의"),
            ("운송", "사고", "충돌", "운송 사고"),

            ("하차지", "수작업", "이동", "하차지 수작업 이동"),
            ("하차지", "수작업", "낙하", "하차지 수작업 낙하"),
            ("하차지", "지게차", "충격", "하차지 지게차 충격"),

            ("가공공정", "업체", "재단 불량", "규격 오가공"),
            ("가공공정", "업체", "제품 파손", "가공 중 파손"),

            ("원자재", "생산", "제품 하자", "초기 불량"),

            ("부상", "지게차", "충격", "지게차 작업 중 부상"),
        ]
        cur.executemany("""
            INSERT OR IGNORE INTO damage_codes (category, type, situation, description)
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
        SELECT id, qty FROM inventory
        WHERE warehouse=? AND location=? AND brand=?
          AND item_code=? AND lot=? AND spec=?
    """, (warehouse, location, brand, item_code, lot, spec))

    row = cur.fetchone()

    if row:
        new_qty = max(0, int(row["qty"]) + int(qty_delta))
        cur.execute("""
            UPDATE inventory
            SET qty=?, item_name=?, note=?, updated_at=?
            WHERE id=?
        """, (new_qty, item_name, note, now, int(row["id"])))
    else:
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name, lot, spec, qty, note, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (warehouse, location, brand, item_code, item_name, lot, spec, max(0, int(qty_delta)), note, now))

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

    where: List[str] = []
    params: List[Any] = []

    warehouse = (warehouse or "").strip()
    location = (location or "").strip()
    brand = (brand or "").strip()
    item_code = (item_code or "").strip()
    lot = (lot or "").strip()
    spec = (spec or "").strip()

    if warehouse:
        where.append("warehouse = ?")
        params.append(warehouse)
    if location:
        where.append("location LIKE ?")
        params.append(f"%{location}%")
    if brand:
        where.append("brand = ?")
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
    params.append(int(limit))

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_inventory_qty(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    lot: str,
    spec: str,
) -> int:
    """단일 키(warehouse/location/brand/item_code/lot/spec) 현재고 qty 반환"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT qty FROM inventory
        WHERE warehouse=? AND location=? AND brand=?
          AND item_code=? AND lot=? AND spec=?
        LIMIT 1
    """, (
        (warehouse or "").strip(),
        (location or "").strip(),
        (brand or "").strip(),
        (item_code or "").strip(),
        (lot or "").strip(),
        (spec or "").strip(),
    ))
    row = cur.fetchone()
    conn.close()
    return int(row["qty"]) if row else 0


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
    """
    ✅ 중복 방어:
      - 모바일에서 같은 submit이 여러 번 들어오는 케이스 방지
      - dedup_seconds(기본 5초) 이내 같은 key면 insert 안함
    """
    now = datetime.now()
    now_str = now.isoformat(timespec="seconds")
    threshold = (now - timedelta(seconds=int(dedup_seconds))).isoformat(timespec="seconds")

    # 정리
    type = (type or "").strip()
    warehouse = (warehouse or "").strip()
    operator = (operator or "").strip()
    brand = (brand or "").strip()
    item_code = (item_code or "").strip()
    item_name = (item_name or "").strip()
    lot = (lot or "").strip()
    spec = (spec or "").strip()
    from_location = (from_location or "").strip()
    to_location = (to_location or "").strip()
    note = (note or "").strip()

    try:
        qty_int = int(qty)
    except Exception:
        qty_int = 0

    conn = get_db()
    cur = conn.cursor()

    # ⚠️ SQLite datetime()에 의존하지 않고, ISO 문자열 비교로 안전하게 처리
    cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM history
        WHERE type=?
          AND warehouse=?
          AND brand=?
          AND item_code=?
          AND lot=?
          AND spec=?
          AND from_location=?
          AND to_location=?
          AND qty=?
          AND created_at >= ?
    """, (
        type, warehouse, brand, item_code, lot, spec,
        from_location, to_location, qty_int,
        threshold,
    ))

    if int((cur.fetchone() or {"cnt": 0})[0]) > 0:
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
        qty_int, note, now_str,
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

    where: List[str] = []
    params: List[Any] = []

    # created_at 예: 2026-01-02T12:34:56
    if year is not None:
        y = f"{int(year):04d}"
        if month is not None:
            m = f"{int(month):02d}"
            if day is not None:
                d = f"{int(day):02d}"
                prefix = f"{y}-{m}-{d}"
            else:
                prefix = f"{y}-{m}"
        else:
            prefix = y

        where.append("created_at LIKE ?")
        params.append(prefix + "%")

    sql = "SELECT * FROM history"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(int(limit))

    cur.execute(sql, params)
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

    where: List[str] = []
    params: List[Any] = []

    category = (category or "").strip()
    type = (type or "").strip()
    situation = (situation or "").strip()

    if active_only:
        where.append("is_active = 1")
    if category:
        where.append("category = ?")
        params.append(category)
    if type:
        where.append("type = ?")
        params.append(type)
    if situation:
        where.append("situation = ?")
        params.append(situation)

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
    qty: int,
    damage_code_id: int,
    detail: str = "",
    deduct_inventory: bool = False,
) -> None:
    """
    CS/파손 이력 저장
    - deduct_inventory=True 이면 재고에서 qty 차감 (옵션)
    """
    now = datetime.now().isoformat(timespec="seconds")

    occurred_at = (occurred_at or "").strip()
    warehouse = (warehouse or "").strip()
    location = (location or "").strip()
    brand = (brand or "").strip()
    item_code = (item_code or "").strip()
    item_name = (item_name or "").strip()
    lot = (lot or "").strip()
    spec = (spec or "").strip()
    detail = (detail or "").strip()

    try:
        qty_int = int(qty)
    except Exception:
        qty_int = 0
    try:
        code_int = int(damage_code_id)
    except Exception:
        code_int = 0

    if qty_int <= 0:
        raise ValueError("qty must be >= 1")
    if code_int <= 0:
        raise ValueError("damage_code_id must be valid")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO damage_history
        (occurred_at, warehouse, location, brand,
         item_code, item_name, lot, spec,
         qty, damage_code_id, detail, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        occurred_at, warehouse, location, brand,
        item_code, item_name, lot, spec,
        qty_int, code_int, detail, now
    ))

    conn.commit()
    conn.close()

    # 옵션: 재고 차감 (별도 트랜잭션, 정책상 damage 이력과 분리)
    if deduct_inventory:
        upsert_inventory(
            warehouse=warehouse,
            location=location,
            brand=brand,
            item_code=item_code,
            item_name=item_name,
            lot=lot,
            spec=spec,
            qty_delta=-qty_int,
            note="CS 차감",
        )


def query_damage_history(
    year: Optional[int] = None,
    month: Optional[int] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()

    where: List[str] = []
    params: List[Any] = []

    if year:
        if month:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{int(year):04d}-{int(month):02d}%")
        else:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{int(year):04d}%")

    sql = """
        SELECT dh.*, dc.category, dc.type, dc.situation
        FROM damage_history dh
        JOIN damage_codes dc ON dh.damage_code_id = dc.id
    """
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY dh.occurred_at DESC, dh.id DESC LIMIT ?"
    params.append(int(limit))

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

    where: List[str] = []
    params: List[Any] = []

    if year:
        if month:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{int(year):04d}-{int(month):02d}%")
        else:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{int(year):04d}%")

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

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.core.paths import DB_PATH


# =====================================================
# DB CONNECTION
# =====================================================

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    # SQLite FK 보호 (논리적 무결성)
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

    # -------------------------------------------------
    # HISTORY (입고 / 출고 / 이동 이력)
    # -------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,              -- inbound / outbound / move
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
            category TEXT NOT NULL,          -- 물류 / 사옥 / 운송 / 하차지 / 가공공정 / 원자재 / 부상
            type TEXT NOT NULL,              -- 수작업 / 지게차 / 업체명 등
            situation TEXT NOT NULL,         -- 이동 / 낙하 / 충격 / 재단불량 등
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
    # NOTE:
    # - 재고 수량을 자동 차감하지 않는다.
    # - 물류 행위(history)와 품질/CS 기록은 의도적으로 분리
    # -------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS damage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_at TEXT NOT NULL,       -- 발생일
            warehouse TEXT NOT NULL,
            location TEXT NOT NULL,
            brand TEXT NOT NULL DEFAULT '',
            item_code TEXT NOT NULL,
            item_name TEXT NOT NULL,
            lot TEXT NOT NULL,
            spec TEXT NOT NULL,
            qty INTEGER NOT NULL,
            damage_code_id INTEGER NOT NULL, -- damage_codes.id
            detail TEXT DEFAULT '',
            created_at TEXT NOT NULL
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
    # DAMAGE CODE SEED (최초 1회만)
    # -------------------------------------------------
    cur.execute("SELECT COUNT(*) FROM damage_codes")
    if cur.fetchone()[0] == 0:
        seed_rows = [
            # 물류
            ("물류", "수작업", "이동", "수작업 이동 중 발생"),
            ("물류", "수작업", "낙하", "수작업 중 낙하"),
            ("물류", "수작업", "충격", "수작업 중 외부 충격"),
            ("물류", "지게차", "이동", "지게차 이동 작업"),
            ("물류", "지게차", "낙하", "지게차 작업 중 낙하"),
            ("물류", "지게차", "충격", "지게차 충돌 / 충격"),
            ("물류", "보관", "적재 기준 미준수", "적재 기준 위반"),
            ("물류", "보관", "장기 적재", "장기 적재로 인한 변형"),

            # 사옥
            ("사옥", "수작업", "이동", "사옥 내 수작업 이동"),
            ("사옥", "수작업", "낙하", "사옥 내 수작업 낙하"),
            ("사옥", "수작업", "충격", "사옥 내 충격"),

            # 운송
            ("운송", "하차", "부주의", "운송 중 부주의"),
            ("운송", "사고", "충돌", "운송 사고"),

            # 하차지
            ("하차지", "수작업", "이동", "하차지 수작업 이동"),
            ("하차지", "수작업", "낙하", "하차지 수작업 낙하"),
            ("하차지", "지게차", "충격", "하차지 지게차 충격"),

            # 가공공정
            ("가공공정", "업체", "재단 불량", "규격 오가공"),
            ("가공공정", "업체", "제품 파손", "가공 중 파손"),

            # 원자재
            ("원자재", "생산", "제품 하자", "초기 불량"),

            # 부상
            ("부상", "지게차", "충격", "지게차 작업 중 부상"),
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
    note: str = ""
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, qty FROM inventory
        WHERE warehouse=? AND location=? AND brand=?
          AND item_code=? AND lot=? AND spec=?
    """, (warehouse, location, brand, item_code, lot, spec))

    row = cur.fetchone()

    if row:
        new_qty = max(0, row["qty"] + qty_delta)
        cur.execute("""
            UPDATE inventory
            SET qty=?, item_name=?, note=?, updated_at=?
            WHERE id=?
        """, (new_qty, item_name, note, now, row["id"]))
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
    qty: int,
    from_location: str = "",
    to_location: str = "",
    note: str = ""
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO history
        (type, warehouse, operator, brand, item_code,
         item_name, lot, spec, from_location, to_location,
         qty, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        type, warehouse, operator, brand, item_code,
        item_name, lot, spec, from_location, to_location,
        qty, note, now
    ))

    conn.commit()
    conn.close()


# =====================================================
# DAMAGE / CS
# =====================================================

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
    detail: str = ""
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
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
        qty, damage_code_id, detail, now
    ))

    conn.commit()
    conn.close()


def list_damage_codes(
    category: str = "",
    type: str = "",
    situation: str = "",
    active_only: bool = True
) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()

    where = []
    params: List[Any] = []

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


def query_damage_history(
    year: Optional[int] = None,
    month: Optional[int] = None,
    limit: int = 500
) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()

    where = []
    params: List[Any] = []

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

    sql += " ORDER BY dh.occurred_at DESC LIMIT ?"
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
    params: List[Any] = []

    if year:
        if month:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{year:04d}-{month:02d}%")
        else:
            where.append("dh.occurred_at LIKE ?")
            params.append(f"{year:04d}%")

    sql = """
        SELECT
            dc.category,
            COUNT(*) AS cnt
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

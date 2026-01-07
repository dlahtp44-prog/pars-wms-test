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
        situation TEXT NOT NULL,     -- 상황: 이동/낙하/충격/적재 기준 미준수/부주의 등
        description TEXT DEFAULT '', -- 설명
        is_active INTEGER NOT NULL DEFAULT 1
    )""")
    cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS ux_damage_codes_key
        ON damage_codes(category, type, situation)""")

    # 초기 기준 데이터 (없을 때만 insert)
    cur.execute("SELECT COUNT(*) FROM damage_codes")
    if cur.fetchone()[0] == 0:
        seed_rows = [
            # 물류
            ("물류", "수작업", "이동", "작업자가 수작업으로 제품을 옮기는 행위"),
            ("물류", "수작업", "낙하", "작업자가 수작업 중 제품을 떨어뜨리는 행위"),
            ("물류", "수작업", "충격", "작업자가 수작업 중 제품이 외부 요인과 부딪히는 행위"),
            ("물류", "지게차", "이동", "지게차 작업 중 제품을 옮기는 행위"),
            ("물류", "지게차", "낙하", "지게차 작업 중 제품을 떨어뜨리는 행위"),
            ("물류", "지게차", "충격", "지게차 작업 중 제품이 외부 요인과 부딪히는 행위(지게차와의 충돌 포함)"),
            ("물류", "보관", "적재 기준 미준수", "불완전한 적재/언패킹 후 보관/제품을 벽에 세워둠 등"),
            ("물류", "보관", "허용 하중 초과", "허용 수치 이상의 하중 적재"),
            ("물류", "보관", "장기 적재", "장기간 적재로 인한 구조적 변형/응력 누적"),

            # 사옥
            ("사옥", "수작업", "이동", "작업자가 수작업으로 제품을 옮기는 행위"),
            ("사옥", "수작업", "낙하", "작업자가 수작업 중 제품을 떨어뜨리는 행위"),
            ("사옥", "수작업", "충격", "작업자가 수작업 중 제품이 외부 요인과 부딪히는 행위"),
            ("사옥", "보관", "적재 기준 미준수", "불완전한 적재/언패킹 후 보관/제품을 벽에 세워둠 등"),

            # 운송
            ("운송", "운송 하차", "부주의", "차량 운전자의 부주의(급정거/급회전/높이 제한 파악 미흡 등)"),
            ("운송", "사고", "충돌", "차량 충돌, 끼절림, 미끄럼 등 물리적 사고"),

            # 하차지
            ("하차지", "수작업", "이동", "하차지에서 수작업으로 제품을 옮기는 행위"),
            ("하차지", "수작업", "낙하", "하차지에서 수작업 중 제품 낙하"),
            ("하차지", "수작업", "충격", "하차지에서 제품이 외부 요인과 부딪힘"),
            ("하차지", "지게차", "이동", "하차지에서 지게차로 제품 이동"),
            ("하차지", "지게차", "낙하", "하차지에서 지게차 작업 중 낙하"),
            ("하차지", "지게차", "충격", "하차지에서 지게차 작업 중 충격/충돌"),

            # 가공공정 (업체/현장별)
            ("가공공정", "삼전스톤", "재단 불량", "주문된 규격이 아닌 다른 규격으로 가공하는 행위"),
            ("가공공정", "삼전스톤", "제품 파손", "가공 작업 중 제품을 파손시키는 행위"),
            ("가공공정", "제이투", "재단 불량", "주문된 규격이 아닌 다른 규격으로 가공하는 행위"),
            ("가공공정", "제이투", "제품 파손", "가공 작업 중 제품을 파손시키는 행위"),
            ("가공공정", "기타", "재단 불량", "주문된 규격이 아닌 다른 규격으로 가공하는 행위"),
            ("가공공정", "기타", "제품 파손", "가공 작업 중 제품을 파손시키는 행위"),

            # 원자재
            ("원자재", "생산", "제품 하자", "제품이 정상 조건이 아닌 상태(크랙/규격 이상/수량 부족 등)"),
            ("원자재", "생산", "중복 보완 미흡", "제품을 보호하는 완충재/포장 상태가 불완전한 상태"),

            # 부상
            ("부상", "지게차", "충격", "지게차 작업 중 제품이 외부 요인과 부딪히는 행위(지게차와의 충돌 포함)"),
        ]
        cur.executemany(
            "INSERT OR IGNORE INTO damage_codes(category, type, situation, description) VALUES(?, ?, ?, ?)",
            seed_rows
        )

    conn.commit()
    conn.close()

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
    """재고 증감(입고/출고/이동 공통).
    KEY: warehouse + location + brand + item_code + lot + spec
    """
    now = datetime.now().isoformat(timespec="seconds")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""SELECT id, qty FROM inventory
        WHERE warehouse=? AND location=? AND brand=? AND item_code=? AND lot=? AND spec=?""",
        (warehouse, location, brand, item_code, lot, spec)
    )
    row = cur.fetchone()

    if row:
        new_qty = int(row["qty"]) + int(qty_delta)
        if new_qty < 0:
            new_qty = 0
        cur.execute("""UPDATE inventory
            SET qty=?, item_name=?, note=?, updated_at=?
            WHERE id=?""",
            (new_qty, item_name, note, now, int(row["id"]))
        )
    else:
        new_qty = int(qty_delta)
        if new_qty < 0:
            new_qty = 0
        cur.execute("""INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name, lot, spec, qty, note, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (warehouse, location, brand, item_code, item_name, lot, spec, new_qty, note, now)
        )

    conn.commit()
    conn.close()

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
    cur.execute("""INSERT INTO history
        (type, warehouse, operator, brand, item_code, item_name, lot, spec, from_location, to_location, qty, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (type, warehouse, operator, brand, item_code, item_name, lot, spec, from_location, to_location, int(qty), note, now)
    )
    conn.commit()
    conn.close()

def query_inventory(
    warehouse: str = "",
    location: str = "",
    brand: str = "",
    item_code: str = "",
    lot: str = "",
    spec: str = "",
    limit: int = 500
) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()

    where = []
    params: list[Any] = []

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

    cur.execute(sql, tuple(params))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def query_history(
    year: str = "",
    month: str = "",
    day: str = "",
    limit: int = 500
) -> List[Dict[str, Any]]:
    """이력 조회.
    - year/month/day 지정 시 created_at(ISO 문자열)의 prefix 기준으로 필터링합니다.
    """
    conn = get_db()
    cur = conn.cursor()

    where = []
    params: list[Any] = []

    # created_at 예: 2026-01-02T12:34:56
    if year:
        y = f"{int(year):04d}"
        if month:
            m = f"{int(month):02d}"
            if day:
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

    cur.execute(sql, tuple(params))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def list_damage_codes(
    category: str = "",
    type: str = "",
    situation: str = "",
    active_only: bool = True,
) -> List[Dict[str, Any]]:
    """파손/CS 분류 코드 조회"""
    conn = get_db()
    cur = conn.cursor()

    where = []
    params: list[Any] = []

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
    sql += " ORDER BY category ASC, type ASC, situation ASC"

    cur.execute(sql, tuple(params))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

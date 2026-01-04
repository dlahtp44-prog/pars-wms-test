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
    cols=[r[1] for r in cur.fetchall()]
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

    # users (simple auth)
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TEXT NOT NULL
    )""")

    # calendar memo (shared memo calendar)
    cur.execute("""CREATE TABLE IF NOT EXISTS calendar_memo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        memo_date TEXT NOT NULL,
        content TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_calendar_date ON calendar_memo(memo_date)""")

    # seed default admin if no user exists
    cur.execute("SELECT COUNT(*) FROM users")
    user_cnt = int(cur.fetchone()[0])
    if user_cnt == 0:
        from app.auth import hash_password
        now = datetime.now().isoformat(timespec='seconds')
        cur.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?,?,?,?)",
            ("admin", hash_password("admin1234"), "admin", now)
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
    brand = brand or ""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, qty FROM inventory
           WHERE warehouse=? AND location=? AND brand=? AND item_code=? AND lot=? AND spec=?""",
        (warehouse, location, brand, item_code, lot, spec),
    )
    row = cur.fetchone()
    if row:
        new_qty = int(row["qty"]) + int(qty_delta)
        if new_qty < 0:
            raise ValueError("재고 부족")
        cur.execute(
            """UPDATE inventory
               SET qty=?, item_name=?, note=COALESCE(NULLIF(?,''), note), updated_at=?
               WHERE id=?""",
            (new_qty, item_name, note, now, row["id"]),
        )
        if new_qty == 0:
            cur.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
    else:
        if int(qty_delta) < 0:
            raise ValueError("재고 부족")
        cur.execute(
            """INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name, lot, spec, qty, note, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (warehouse, location, brand, item_code, item_name, lot, spec, int(qty_delta), note, now),
        )
    conn.commit()
    conn.close()

def add_history(
    type_: str,
    warehouse: str,
    operator: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    from_location: str,
    to_location: str,
    qty: int,
    note: str = "",
) -> None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO history
        (type, warehouse, operator, brand, item_code, item_name, lot, spec, from_location, to_location, qty, note, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            type_,
            warehouse,
            operator or "",
            brand or "",
            item_code,
            item_name,
            lot,
            spec,
            from_location or "",
            to_location or "",
            int(qty),
            note,
            datetime.now().isoformat(timespec="seconds"),
        ),
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
) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    q = "SELECT * FROM inventory WHERE 1=1"
    params: List[Any] = []
    if warehouse:
        q += " AND warehouse=?"
        params.append(warehouse)
    if location:
        q += " AND location=?"
        params.append(location)
    if brand:
        q += " AND brand=?"
        params.append(brand)
    if item_code:
        q += " AND item_code LIKE ?"
        params.append(f"%{item_code}%")
    if lot:
        q += " AND lot=?"
        params.append(lot)
    if spec:
        q += " AND spec=?"
        params.append(spec)
    q += " ORDER BY updated_at DESC, location ASC"
    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def query_history(limit: int = 200, year: int | None = None, month: int | None = None, day: int | None = None) -> List[Dict[str, Any]]:
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


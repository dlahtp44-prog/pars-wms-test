import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.core.paths import DB_PATH

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT NOT NULL,
        location TEXT NOT NULL,
        item_code TEXT NOT NULL,
        item_name TEXT NOT NULL,
        lot TEXT NOT NULL,
        spec TEXT NOT NULL,
        qty INTEGER NOT NULL DEFAULT 0,
        note TEXT DEFAULT '',
        updated_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_inventory_key
        ON inventory(warehouse, location, item_code, lot, spec)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL, -- 입고/출고/이동
        warehouse TEXT NOT NULL,
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
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_history_created
        ON history(created_at)""")

    conn.commit()
    conn.close()

def upsert_inventory(warehouse: str, location: str, item_code: str, item_name: str, lot: str, spec: str, qty_delta: int, note: str="") -> None:
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""SELECT id, qty FROM inventory
                   WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?""",
                (warehouse, location, item_code, lot, spec))
    row = cur.fetchone()
    if row:
        new_qty = int(row["qty"]) + int(qty_delta)
        if new_qty < 0:
            raise ValueError("재고 부족")
        cur.execute("""UPDATE inventory
                       SET qty=?, item_name=?, note=COALESCE(NULLIF(?,''), note), updated_at=?
                       WHERE id=?""",
                    (new_qty, item_name, note, now, row["id"]))
        if new_qty == 0:
            cur.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
    else:
        if int(qty_delta) < 0:
            raise ValueError("재고 부족")
        cur.execute("""INSERT INTO inventory
            (warehouse, location, item_code, item_name, lot, spec, qty, note, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (warehouse, location, item_code, item_name, lot, spec, int(qty_delta), note, now)
        )
    conn.commit()
    conn.close()

def add_history(type_: str, warehouse: str, item_code: str, item_name: str, lot: str, spec: str,
                from_location: str, to_location: str, qty: int, note: str="") -> None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""INSERT INTO history
        (type, warehouse, item_code, item_name, lot, spec, from_location, to_location, qty, note, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (type_, warehouse, item_code, item_name, lot, spec, from_location, to_location, int(qty), note, datetime.now().isoformat(timespec="seconds"))
    )
    conn.commit()
    conn.close()

def query_inventory(location: str="", item_code: str="", lot: str="", spec: str="") -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    q = "SELECT warehouse, location, item_code, item_name, lot, spec, qty, note, updated_at FROM inventory WHERE 1=1"
    params=[]
    if location:
        q += " AND location LIKE ?"
        params.append(f"%{location}%")
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
    rows=[dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def query_history(limit: int=200) -> List[Dict[str, Any]]:
    conn=get_db()
    cur=conn.cursor()
    cur.execute("""SELECT type, warehouse, item_code, item_name, lot, spec,
        from_location, to_location, qty, note, created_at
        FROM history ORDER BY created_at DESC LIMIT ?""", (int(limit),))
    rows=[dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.paths import DB_PATH

# =========================================================
# DB connection
# =========================================================
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
    """v1.7.0-stable 기준 DB + v1.8 확장(로그인/CS/달력메모)"""
    conn = get_db()
    cur = conn.cursor()

    # -------------------------
    # inventory (현재고)
    # -------------------------
    cur.execute(
        """CREATE TABLE IF NOT EXISTS inventory (
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
        )"""
    )
    cur.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS uq_inventory_key
           ON inventory(warehouse, location, brand, item_code, lot, spec)"""
    )
    cur.execute(
        """CREATE INDEX IF NOT EXISTS idx_inventory_item
           ON inventory(item_code, item_name)"""
    )
    _ensure_column(cur, "inventory", "brand", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(cur, "inventory", "updated_at", "TEXT NOT NULL DEFAULT ''")

    # -------------------------
    # history (이력)
    # -------------------------
    cur.execute(
        """CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL, -- inbound/outbound/move
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
        )"""
    )
    _ensure_column(cur, "history", "brand", "TEXT NOT NULL DEFAULT ''")
    cur.execute(
        """CREATE INDEX IF NOT EXISTS idx_history_created
           ON history(created_at)"""
    )

    # =========================================================
    # v1.8 additions
    # =========================================================

    # users (간단 관리자)
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )"""
    )

    # sessions (cookie token)
    cur.execute(
        """CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )"""
    )
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)""")

    # cs tickets (CS 관리)
    cur.execute(
        """CREATE TABLE IF NOT EXISTS cs_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_date TEXT NOT NULL,   -- YYYY-MM-DD
            customer TEXT NOT NULL DEFAULT '',
            channel TEXT NOT NULL DEFAULT '', -- 전화/카톡/메일 등
            order_no TEXT NOT NULL DEFAULT '',
            item_code TEXT NOT NULL DEFAULT '',
            item_name TEXT NOT NULL DEFAULT '',
            issue_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'open', -- open/doing/done
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )"""
    )
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_cs_created_date ON cs_tickets(created_date)""")

    # memos (월 달력 메모) - 추후 화면 연동용
    cur.execute(
        """CREATE TABLE IF NOT EXISTS memos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memo_date TEXT NOT NULL, -- YYYY-MM-DD
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_memos_date ON memos(memo_date)""")

    conn.commit()
    conn.close()

    # default admin
    _ensure_default_admin()


# =========================================================
# Inventory / History helpers (v1.7 stable)
# =========================================================
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
    """재고 증감(입고/출고/이동 공통).
    KEY: warehouse + location + brand + item_code + lot + spec
    """
    now = datetime.now().isoformat(timespec="seconds")
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
            conn.close()
            raise ValueError("재고 부족")
        cur.execute(
            """UPDATE inventory
               SET qty=?, note=?, item_name=?, updated_at=?
               WHERE id=?""",
            (new_qty, note, item_name, now, int(row["id"])),
        )
    else:
        if int(qty_delta) < 0:
            conn.close()
            raise ValueError("재고 부족")
        cur.execute(
            """INSERT INTO inventory
               (warehouse, location, brand, item_code, item_name, lot, spec, qty, note, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
    created_at = datetime.now().isoformat(timespec="seconds")
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO history
           (type, warehouse, operator, brand, item_code, item_name, lot, spec,
            from_location, to_location, qty, note, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            type_,
            warehouse,
            operator,
            brand,
            item_code,
            item_name,
            lot,
            spec,
            from_location,
            to_location,
            int(qty),
            note,
            created_at,
        ),
    )
    conn.commit()
    conn.close()


def query_inventory(
    q: str = "",
    warehouse: str = "",
    location: str = "",
    item_code: str = "",
    lot: str = "",
    brand: str = "",
    limit: int = 500,
) -> List[Dict[str, Any]]:
    """현재고 조회 (이력과 분리)"""
    conn = get_db()
    cur = conn.cursor()

    where = []
    params: List[Any] = []

    if q:
        where.append("(item_code LIKE ? OR item_name LIKE ? OR lot LIKE ? OR spec LIKE ? OR location LIKE ?)")
        like = f"%{q}%"
        params += [like, like, like, like, like]
    if warehouse:
        where.append("warehouse = ?")
        params.append(warehouse)
    if location:
        where.append("location = ?")
        params.append(location)
    if item_code:
        where.append("item_code = ?")
        params.append(item_code)
    if lot:
        where.append("lot = ?")
        params.append(lot)
    if brand:
        where.append("brand = ?")
        params.append(brand)

    sql = "SELECT * FROM inventory"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY updated_at DESC, id DESC LIMIT ?"
    params.append(int(limit))

    cur.execute(sql, tuple(params))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def query_history(
    q: str = "",
    type_: str = "",
    created_prefix: str = "",
    limit: int = 500,
) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()

    where = []
    params: List[Any] = []

    if q:
        where.append("(item_code LIKE ? OR item_name LIKE ? OR lot LIKE ? OR spec LIKE ? OR from_location LIKE ? OR to_location LIKE ?)")
        like = f"%{q}%"
        params += [like, like, like, like, like, like]
    if type_:
        where.append("type = ?")
        params.append(type_)
    if created_prefix:
        # YYYY-MM or YYYY-MM-DD
        where.append("created_at LIKE ?")
        params.append(created_prefix + "%")

    sql = "SELECT * FROM history"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(int(limit))

    cur.execute(sql, tuple(params))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================================================
# Auth (v1.8)
# =========================================================
import secrets
import hashlib

def _hash_password(password: str, salt: str) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return dk.hex()

def make_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    return f"pbkdf2_sha256${salt}${_hash_password(password, salt)}"

def verify_password(password: str, password_hash: str) -> bool:
    try:
        algo, salt, digest = password_hash.split("$", 2)
        if algo != "pbkdf2_sha256":
            return False
        return _hash_password(password, salt) == digest
    except Exception:
        return False

def _ensure_default_admin() -> None:
    """기본 admin 계정 생성 (없을 때만).
    배포 전에는 환경변수로 바꾸는 것을 권장.
    """
    username = os.getenv("PARS_ADMIN_USER", "admin")
    password = os.getenv("PARS_ADMIN_PASS", "admin")
    now = datetime.now().isoformat(timespec="seconds")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO users(username, password_hash, role, is_active, created_at) VALUES(?, ?, 'admin', 1, ?)",
            (username, make_password_hash(password), now),
        )
        conn.commit()
    conn.close()

def create_session(username: str, password: str, hours: int = 24) -> Optional[str]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash, is_active FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    if not user or int(user["is_active"]) != 1:
        conn.close()
        return None
    if not verify_password(password, user["password_hash"]):
        conn.close()
        return None

    token = secrets.token_urlsafe(32)
    now = datetime.now()
    expires = now + timedelta(hours=hours)
    cur.execute(
        "INSERT INTO sessions(token, user_id, created_at, expires_at) VALUES(?, ?, ?, ?)",
        (token, int(user["id"]), now.isoformat(timespec="seconds"), expires.isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()
    return token

def get_user_by_session(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """SELECT u.id, u.username, u.role, u.is_active, s.expires_at
             FROM sessions s JOIN users u ON u.id=s.user_id
             WHERE s.token=?""",
        (token,),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    try:
        exp = datetime.fromisoformat(row["expires_at"])
        if exp < datetime.now():
            # cleanup
            cur.execute("DELETE FROM sessions WHERE token=?", (token,))
            conn.commit()
            conn.close()
            return None
    except Exception:
        conn.close()
        return None

    user = dict(row)
    conn.close()
    return user

def delete_session(token: str) -> None:
    if not token:
        return
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE token=?", (token,))
    conn.commit()
    conn.close()


# =========================================================
# CS (v1.8)
# =========================================================
def create_cs_ticket(data: Dict[str, Any]) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    created_date = data.get("created_date") or datetime.now().date().isoformat()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO cs_tickets
           (created_date, customer, channel, order_no, item_code, item_name, issue_type, status, note, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            created_date,
            data.get("customer", ""),
            data.get("channel", ""),
            data.get("order_no", ""),
            data.get("item_code", ""),
            data.get("item_name", ""),
            data.get("issue_type", ""),
            data.get("status", "open"),
            data.get("note", ""),
            now,
        ),
    )
    tid = cur.lastrowid
    conn.commit()
    conn.close()
    return int(tid)

def list_cs_tickets(year: int, month: int) -> List[Dict[str, Any]]:
    ym = f"{year:04d}-{month:02d}"
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """SELECT * FROM cs_tickets
           WHERE created_date LIKE ?
           ORDER BY created_date DESC, id DESC""",
        (ym + "%",),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def update_cs_ticket(ticket_id: int, fields: Dict[str, Any]) -> None:
    allow = {"created_date","customer","channel","order_no","item_code","item_name","issue_type","status","note"}
    sets=[]
    params=[]
    for k,v in fields.items():
        if k in allow:
            sets.append(f"{k}=?")
            params.append(v)
    if not sets:
        return
    params.append(int(ticket_id))
    conn=get_db()
    cur=conn.cursor()
    cur.execute(f"UPDATE cs_tickets SET {', '.join(sets)} WHERE id=?", tuple(params))
    conn.commit()
    conn.close()

def delete_cs_ticket(ticket_id: int) -> None:
    conn=get_db()
    cur=conn.cursor()
    cur.execute("DELETE FROM cs_tickets WHERE id=?", (int(ticket_id),))
    conn.commit()
    conn.close()

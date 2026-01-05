import os, sqlite3
from contextlib import contextmanager
DB_PATH=os.getenv("WMS_DB","WMS.db")
def get_conn():
    conn=sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory=sqlite3.Row
    return conn
def init_db():
    conn=get_conn();cur=conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT NOT NULL,
        location TEXT NOT NULL,
        brand TEXT DEFAULT '',
        item_code TEXT NOT NULL,
        item_name TEXT NOT NULL,
        lot TEXT NOT NULL,
        spec TEXT NOT NULL,
        qty INTEGER NOT NULL DEFAULT 0,
        note TEXT DEFAULT '',
        updated_at TEXT NOT NULL
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_key ON inventory(warehouse,location,item_code,lot,spec)")
    cur.execute("""CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        type TEXT NOT NULL,
        warehouse TEXT NOT NULL,
        location TEXT DEFAULT '',
        from_location TEXT DEFAULT '',
        to_location TEXT DEFAULT '',
        brand TEXT DEFAULT '',
        item_code TEXT DEFAULT '',
        item_name TEXT DEFAULT '',
        lot TEXT DEFAULT '',
        spec TEXT DEFAULT '',
        qty INTEGER DEFAULT 0,
        note TEXT DEFAULT '',
        operator TEXT DEFAULT ''
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_history_date ON history(created_at)")
    cur.execute("""CREATE TABLE IF NOT EXISTS calendar_memo(
        memo_date TEXT PRIMARY KEY,
        memo TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")
    conn.commit();conn.close()
@contextmanager
def db():
    conn=get_conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from app.core.paths import DB_PATH

# =====================================================
# DB CONNECTION & UTILS
# =====================================================

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _q3(val) -> float:
    if val is None: return 0.0
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

        # 재고 테이블
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
        cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_key ON inventory (warehouse, location, brand, item_code, lot, spec)")

        # 일반 이력 테이블
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
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON history (created_at)")

        # 파손 코드 마스터
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
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_damage_codes_key ON damage_codes (category, type, situation)")

        # 파손 발생 이력
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

        # 초기 데이터 삽입
        cur.execute("SELECT COUNT(*) FROM damage_codes")
        if cur.fetchone()[0] == 0:
            cur.executemany("""
                INSERT INTO damage_codes (category, type, situation, description)
                VALUES (?, ?, ?, ?)
            """, [
                ("물류", "수작업", "이동", "수작업 이동 중 발생"),
                ("물류", "수작업", "낙하", "수작업 중 낙하"),
                ("물류", "지게차", "충격", "지게차 충돌"),
                ("운송", "하차", "부주의", "하차 중 파손"),
                ("가공", "업체", "불량", "가공 불량"),
            ])

        conn.commit()
    finally:
        conn.close()

# =====================================================
# INVENTORY (현재고 & 안전 로직 반영)
# =====================================================

def query_inventory(warehouse=None, location=None, brand=None, item_code=None, lot=None, spec=None, limit=500):
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = ["qty > 0"], []
        if warehouse: where.append("warehouse=?"); params.append(_norm(warehouse))
        if location: where.append("location LIKE ?"); params.append(f"%{_norm(location)}%")
        if brand: where.append("brand=?"); params.append(_norm(brand))
        if item_code: where.append("item_code LIKE ?"); params.append(f"%{_norm(item_code)}%")
        if lot: where.append("lot LIKE ?"); params.append(f"%{_norm(lot)}%")
        if spec: where.append("spec LIKE ?"); params.append(f"%{_norm(spec)}%")
        
        sql = "SELECT * FROM inventory WHERE " + " AND ".join(where) + " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally: conn.close()

def upsert_inventory(warehouse, location, brand, item_code, item_name, lot, spec, qty_delta, note=""):
    """✅ 재고 부족 시 차단 & 0 시 삭제 로직 포함"""
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        delta = _q3(qty_delta)
        w, l, b, ic, iname, lt, sp = map(_norm, [warehouse, location, brand, item_code, item_name, lot, spec])

        cur.execute("SELECT id, qty FROM inventory WHERE warehouse=? AND location=? AND brand=? AND item_code=? AND lot=? AND spec=?", (w, l, b, ic, lt, sp))
        row = cur.fetchone()

        if row:
            current = float(row["qty"])
            if delta < 0 and current < abs(delta): return False # 재고 부족
            new_qty = _q3(current + delta)
            if new_qty <= 0:
                cur.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
            else:
                cur.execute("UPDATE inventory SET qty=?, note=?, updated_at=? WHERE id=?", (new_qty, _norm(note), now, row["id"]))
        else:
            if delta <= 0: return False # 재고 없는데 출고 불가
            cur.execute("INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot, spec, qty, note, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (w, l, b, ic, iname, lt, sp, delta, _norm(note), now))
        
        conn.commit()
        return True
    finally: conn.close()

# =====================================================
# HISTORY (입출입 이력)
# =====================================================

def add_history(type, warehouse, operator, brand, item_code, item_name, lot, spec, from_location, to_location, qty, note="", dedup_seconds=5):
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now()
        threshold = (now - timedelta(seconds=dedup_seconds)).isoformat(timespec="seconds")
        q = _q3(qty)
        # 중복 방지
        cur.execute("SELECT COUNT(*) FROM history WHERE type=? AND warehouse=? AND item_code=? AND lot=? AND spec=? AND from_location=? AND to_location=? AND ABS(qty - ?) < 0.0005 AND created_at >= ?", (_norm(type), _norm(warehouse), _norm(item_code), _norm(lot), _norm(spec), _norm(from_location), _norm(to_location), q, threshold))
        if cur.fetchone()[0] > 0: return
        
        cur.execute("INSERT INTO history (type, warehouse, operator, brand, item_code, item_name, lot, spec, from_location, to_location, qty, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (_norm(type), _norm(warehouse), _norm(operator), _norm(brand), _norm(item_code), _norm(item_name), _norm(lot), _norm(spec), _norm(from_location), _norm(to_location), q, _norm(note), now.isoformat(timespec="seconds")))
        conn.commit()
    finally: conn.close()

def query_history(year=None, month=None, day=None, limit=500):
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []
        if year:
            pat = f"{year:04d}"
            if month:
                pat += f"-{month:02d}"
                if day: pat += f"-{day:02d}"
            where.append("created_at LIKE ?"); params.append(f"{pat}%")
        sql = "SELECT * FROM history"
        if where: sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally: conn.close()

# =====================================================
# DAMAGE / CS (핵심 수정 사항) ✅
# =====================================================

def list_damage_codes(category="", type="", situation="", active_only=True):
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []
        if active_only: where.append("is_active=1")
        if category: where.append("category=?"); params.append(_norm(category))
        if type: where.append("type=?"); params.append(_norm(type))
        if situation: where.append("situation=?"); params.append(_norm(situation))
        
        sql = "SELECT * FROM damage_codes"
        if where: sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY category, type, situation"
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally: conn.close()

def query_damage_history(year=None, month=None, limit=500):
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []
        if year:
            pat = f"{year:04d}"
            if month: pat += f"-{month:02d}"
            where.append("dh.occurred_at LIKE ?"); params.append(f"{pat}%")
        
        sql = """
            SELECT dh.*, dc.category, dc.type, dc.situation
            FROM damage_history dh
            JOIN damage_codes dc ON dh.damage_code_id = dc.id
        """
        if where: sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY dh.occurred_at DESC, dh.id DESC LIMIT ?"
        params.append(limit)
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally: conn.close()

def query_damage_summary_by_category(year=None, month=None):
    """✅ 에러 해결용: 파손 통계 요약"""
    conn = get_db()
    try:
        cur = conn.cursor()
        where, params = [], []
        if year:
            pat = f"{year:04d}"
            if month: pat += f"-{month:02d}"
            where.append("dh.occurred_at LIKE ?"); params.append(f"{pat}%")

        sql = """
            SELECT dc.category, COUNT(*) AS cnt
            FROM damage_history dh
            JOIN damage_codes dc ON dh.damage_code_id = dc.id
        """
        if where: sql += " WHERE " + " AND ".join(where)
        sql += " GROUP BY dc.category ORDER BY cnt DESC"
        
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally: conn.close()

def add_damage_history(data: Dict[str, Any]):
    """✅ 파손 내역 기록용 함수"""
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        cur.execute("""
            INSERT INTO damage_history (
                occurred_at, warehouse, location, brand, item_code, 
                item_name, lot, spec, qty, damage_code_id, detail, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['occurred_at'], data['warehouse'], data['location'], data.get('brand', ''),
            data['item_code'], data['item_name'], data['lot'], data['spec'],
            _q3(data['qty']), data['damage_code_id'], data.get('detail', ''), now
        ))
        conn.commit()
    finally: conn.close()

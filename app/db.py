import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from app.core.paths import DB_PATH

# =====================================================
# DB CONNECTION & UTILS
# =====================================================

def get_db() -> sqlite3.Connection:
    """DB 연결 생성 및 설정"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _q3(val) -> float:
    """소수점 3자리 반올림 고정 (부동소수점 오차 방지)"""
    if val is None: return 0.0
    return float(
        Decimal(str(val)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)
    )

def _norm(v: Optional[str]) -> str:
    """문자열 공백 제거 및 None 처리"""
    return (v or "").strip()

# =====================================================
# INIT / MIGRATION
# =====================================================

def init_db() -> None:
    """데이터베이스 테이블 및 인덱스 초기화"""
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
        # 이력 테이블
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
        cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_key ON inventory (warehouse, location, brand, item_code, lot, spec)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON history (created_at)")
        conn.commit()
    finally:
        conn.close()

# =====================================================
# INVENTORY (현재고 관리)
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
    """✅ 현재고 조회 (수량이 0보다 큰 실재고만 표시)"""
    conn = get_db()
    try:
        cur = conn.cursor()
        where = ["qty > 0"]
        params: List[Any] = []

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
        params.append(limit)

        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def upsert_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    qty_delta: float,
    note: str = "",
) -> bool:
    """
    ✅ 재고 증감 및 자동 정리
    - qty_delta < 0 (출고) 시 현재고보다 많이 나갈 수 없도록 방어
    - 재고 0 이하 도달 시 해당 row 자동 삭제 (데이터 최적화)
    - 반환값: 성공 시 True, 재고 부족 등 실패 시 False
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now().isoformat(timespec="seconds")
        delta = _q3(qty_delta)
        w, l, b, ic, iname, lt, sp = map(_norm, [warehouse, location, brand, item_code, item_name, lot, spec])

        cur.execute("""
            SELECT id, qty FROM inventory 
            WHERE warehouse=? AND location=? AND brand=? AND item_code=? AND lot=? AND spec=?
        """, (w, l, b, ic, lt, sp))
        row = cur.fetchone()

        if row:
            current_qty = float(row["qty"])
            # 출고 시 재고 부족 검증
            if delta < 0 and current_qty < abs(delta):
                return False 
            
            new_qty = _q3(current_qty + delta)
            if new_qty <= 0:
                cur.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
            else:
                cur.execute("UPDATE inventory SET qty=?, note=?, updated_at=? WHERE id=?", (new_qty, _norm(note), now, row["id"]))
        else:
            # 신규 입고인 경우만 생성 (출고인데 기존 재고 없으면 실패)
            if delta <= 0:
                return False
            cur.execute("""
                INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot, spec, qty, note, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (w, l, b, ic, iname, lt, sp, delta, _norm(note), now))
        
        conn.commit()
        return True
    finally:
        conn.close()

# =====================================================
# HISTORY (이력 관리)
# =====================================================

def add_history(
    type: str, warehouse: str, operator: str, brand: str, item_code: str, item_name: str,
    lot: str, spec: str, from_location: str, to_location: str, qty: float, note: str = "", dedup_seconds: int = 5
) -> None:
    """✅ 입/출고/이동 이력 기록 (중복 방지 포함)"""
    conn = get_db()
    try:
        cur = conn.cursor()
        now = datetime.now()
        threshold = (now - timedelta(seconds=dedup_seconds)).isoformat(timespec="seconds")
        q = _q3(qty)

        cur.execute("""
            SELECT COUNT(*) FROM history 
            WHERE type=? AND warehouse=? AND item_code=? AND lot=? AND spec=? AND from_location=? AND to_location=? 
            AND ABS(qty - ?) < 0.0005 AND created_at >= ?
        """, (_norm(type), _norm(warehouse), _norm(item_code), _norm(lot), _norm(spec), _norm(from_location), _norm(to_location), q, threshold))

        if cur.fetchone()[0] > 0: return

        cur.execute("""
            INSERT INTO history (type, warehouse, operator, brand, item_code, item_name, lot, spec, from_location, to_location, qty, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (_norm(type), _norm(warehouse), _norm(operator), _norm(brand), _norm(item_code), _norm(item_name), _norm(lot), _norm(spec), _norm(from_location), _norm(to_location), q, _norm(note), now.isoformat(timespec="seconds")))
        conn.commit()
    finally:
        conn.close()

def query_history(year: Optional[int] = None, month: Optional[int] = None, day: Optional[int] = None, limit: int = 500) -> List[Dict[str, Any]]:
    """✅ 통합 이력 조회"""
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
    finally:
        conn.close()

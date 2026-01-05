from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from ..db import get_db

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

class InventoryRow(BaseModel):
    warehouse: str
    location: str
    brand: str = ""
    item_code: str
    item_name: str
    lot: str = ""
    spec: str = ""
    qty: int
    note: str = ""

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@router.get("")
def list_inventory(limit: int = Query(200, ge=1, le=2000), warehouse: str | None = None, location: str | None = None):
    with get_db() as conn:
        cur = conn.cursor()
        q = "SELECT * FROM inventory WHERE 1=1"
        params=[]
        if warehouse:
            q += " AND warehouse=?"
            params.append(warehouse)
        if location:
            q += " AND location=?"
            params.append(location)
        q += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        rows = cur.execute(q, params).fetchall()
        return [dict(r) for r in rows]

def upsert_inventory(conn, *, warehouse, location, brand, item_code, item_name, lot, spec, delta_qty, note=""):
    cur = conn.cursor()
    existing = cur.execute(
        """SELECT qty FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?""",
        (warehouse, location, item_code, lot, spec)
    ).fetchone()
    now=_now()
    if existing is None:
        new_qty = delta_qty
        if new_qty < 0:
            raise HTTPException(status_code=400, detail="재고가 없습니다.")
        cur.execute(
            """INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot, spec, qty, note, updated_at)
                 VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (warehouse, location, brand, item_code, item_name, lot, spec, new_qty, note, now)
        )
        return new_qty
    else:
        new_qty = int(existing["qty"]) + int(delta_qty)
        if new_qty < 0:
            raise HTTPException(status_code=400, detail="재고 부족")
        cur.execute(
            """UPDATE inventory SET brand=?, item_name=?, qty=?, note=?, updated_at=? 
                 WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?""",
            (brand, item_name, new_qty, note, now, warehouse, location, item_code, lot, spec)
        )
        return new_qty

def add_history(conn, *, type, warehouse="", location="", from_location="", to_location="", brand="", item_code="", item_name="", lot="", spec="", qty=0, note="", operator=""):
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO history (created_at, type, warehouse, location, from_location, to_location, brand, item_code, item_name, lot, spec, qty, note, operator)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (_now(), type, warehouse, location, from_location, to_location, brand, item_code, item_name, lot, spec, int(qty or 0), note, operator)
    )


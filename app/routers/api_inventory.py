from fastapi import APIRouter, Query
from app.db import get_db

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("")
def inventory_list(
    warehouse: str = Query("", description="창고"),
    location: str = Query("", description="로케이션"),
    item_code: str = Query("", description="품번"),
    lot: str = Query("", description="LOT"),
    spec: str = Query("", description="규격"),
    limit: int = Query(200, ge=1, le=2000),
):
    conn = get_db()
    cur = conn.cursor()

    where = []
    params = {}

    if warehouse.strip():
        where.append("warehouse LIKE :warehouse")
        params["warehouse"] = f"%{warehouse.strip()}%"

    if location.strip():
        where.append("location LIKE :location")
        params["location"] = f"%{location.strip()}%"

    if item_code.strip():
        where.append("item_code LIKE :item_code")
        params["item_code"] = f"%{item_code.strip()}%"

    if lot.strip():
        where.append("lot LIKE :lot")
        params["lot"] = f"%{lot.strip()}%"

    if spec.strip():
        where.append("spec LIKE :spec")
        params["spec"] = f"%{spec.strip()}%"

    sql = """
        SELECT id, warehouse, location, item_code, item_name, lot, spec, qty, note, updated_at
        FROM inventory
    """
    if where:
        sql += " WHERE " + " AND ".join(where)

    sql += " ORDER BY updated_at DESC, id DESC LIMIT :limit"
    params["limit"] = limit

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "warehouse": r[1],
            "location": r[2],
            "item_code": r[3],
            "item_name": r[4],
            "lot": r[5],
            "spec": r[6],
            "qty": r[7],
            "note": r[8],
            "updated_at": r[9],
        }
        for r in rows
    ]

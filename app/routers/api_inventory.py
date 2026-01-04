from fastapi import APIRouter, Query
from app.db import get_db

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("")
def get_inventory(
    location: str | None = Query(None),
    limit: int = Query(200)
):
    conn = get_db()
    cur = conn.cursor()

    where = []
    params = []

    if location:
        where.append("location = ?")
        params.append(location.strip())

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    sql = f"""
        SELECT
            id,
            warehouse,
            location,
            item_code,
            item_name,
            lot,
            spec,
            qty
        FROM inventory
        {where_sql}
        ORDER BY id DESC
        LIMIT ?
    """

    cur.execute(sql, params + [limit])
    rows = cur.fetchall()

    columns = [
        "id",
        "warehouse",
        "location",
        "item_code",
        "item_name",
        "lot",
        "spec",
        "qty",
    ]

    return [dict(zip(columns, row)) for row in rows]

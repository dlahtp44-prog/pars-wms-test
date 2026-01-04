from fastapi import APIRouter, Query
from app.db import get_db

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("")
def get_history(
    year: int | None = Query(None),
    month: int | None = Query(None),
    day: int | None = Query(None),
    limit: int = Query(200)
):
    conn = get_db()
    cur = conn.cursor()

    where = []
    params = []

    if year:
        where.append("strftime('%Y', created_at) = ?")
        params.append(f"{year:04d}")
    if month:
        where.append("strftime('%m', created_at) = ?")
        params.append(f"{month:02d}")
    if day:
        where.append("strftime('%d', created_at) = ?")
        params.append(f"{day:02d}")

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    sql = f"""
        SELECT
            id,
            created_at,
            type,
            warehouse,
            item_code,
            item_name,
            lot,
            spec,
            from_location,
            to_location,
            qty,
            remark
        FROM history
        {where_sql}
        ORDER BY created_at DESC
        LIMIT ?
    """

    params.append(limit)
    cur.execute(sql, params)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "created_at": r[1],
            "type": r[2],
            "warehouse": r[3],
            "item_code": r[4],
            "item_name": r[5],
            "lot": r[6],
            "spec": r[7],
            "from": r[8],
            "to": r[9],
            "qty": r[10],
            "remark": r[11],
        }
        for r in rows
    ]

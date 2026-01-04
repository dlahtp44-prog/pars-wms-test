from fastapi import APIRouter, Query
from app.db import get_db

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("")
def get_history(
    year: int | None = Query(None),
    month: int | None = Query(None),
    day: int | None = Query(None),
    limit: int = Query(200),
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

    where_sql = " AND ".join(where)
    if where_sql:
        where_sql = "WHERE " + where_sql

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
            qty
        FROM history
        {where_sql}
        ORDER BY id DESC
        LIMIT ?
    """

    cur.execute(sql, params + [limit])
    rows = cur.fetchall()

    columns = [
        "id",
        "created_at",
        "type",
        "warehouse",
        "item_code",
        "item_name",
        "lot",
        "spec",
        "from_location",
        "to_location",
        "qty",
    ]

    return [dict(zip(columns, row)) for row in rows]

from fastapi import APIRouter, Query
from ..db import get_db

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("")
def list_history(
    limit: int = Query(200, ge=1, le=2000),
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
):
    with get_db() as conn:
        cur = conn.cursor()
        q="SELECT * FROM history WHERE 1=1"
        params=[]
        if year:
            q += " AND substr(created_at,1,4)=?"
            params.append(f"{year:04d}")
        if month:
            q += " AND substr(created_at,6,2)=?"
            params.append(f"{month:02d}")
        if day:
            q += " AND substr(created_at,9,2)=?"
            params.append(f"{day:02d}")
        q += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(limit)
        rows=cur.execute(q, params).fetchall()
        return [dict(r) for r in rows]

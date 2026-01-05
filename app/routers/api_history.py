from fastapi import APIRouter, Query
from app.db import db
router=APIRouter(prefix="/api/history", tags=["history"])
@router.get("")
def list_history(limit:int=Query(200,ge=1,le=5000)):
    with db() as conn:
        rows=conn.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall()
    return {"rows":[dict(r) for r in rows]}

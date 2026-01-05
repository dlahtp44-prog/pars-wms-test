from fastapi import APIRouter, Query
from app.db import db
router=APIRouter(prefix="/api/inventory", tags=["inventory"])
@router.get("")
def list_inventory(limit:int=Query(200,ge=1,le=5000), warehouse:str|None=None, location:str|None=None):
    q="SELECT * FROM inventory"; where=[]; params=[]
    if warehouse: where.append("warehouse=?"); params.append(warehouse)
    if location: where.append("location=?"); params.append(location)
    if where: q+=" WHERE "+" AND ".join(where)
    q+=" ORDER BY updated_at DESC LIMIT ?"; params.append(limit)
    with db() as conn:
        rows=conn.execute(q,params).fetchall()
    return {"rows":[dict(r) for r in rows]}

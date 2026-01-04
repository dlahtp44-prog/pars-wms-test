from fastapi import APIRouter, Form, HTTPException
from app.db import upsert_inventory, add_history

router = APIRouter(prefix="/api/move", tags=["api-move"])

@router.post("")
def move(
    warehouse: str = Form(...),
    operator: str = Form(""),
    brand: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: int = Form(...),
    note: str = Form("")
):
    if qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")
    # 빼기/더하기
    upsert_inventory(warehouse, from_location, brand, item_code, item_name, lot, spec, -qty, note)
    upsert_inventory(warehouse, to_location, brand, item_code, item_name, lot, spec, qty, note)
    add_history("이동", warehouse, operator, brand, item_code, item_name, lot, spec, from_location, to_location, qty, note)
    return {"ok": True}

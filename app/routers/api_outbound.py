from fastapi import APIRouter, Form, HTTPException
from app.db import upsert_inventory, add_history

router = APIRouter(prefix="/api/outbound", tags=["api-outbound"])

@router.post("")
def outbound(
    warehouse: str = Form(...),
    location: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: int = Form(...),
    note: str = Form("")
):
    if qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")
    # 출고는 음수 delta
    upsert_inventory(warehouse, location, item_code, item_name, lot, spec, -qty, note)
    add_history("출고", warehouse, item_code, item_name, lot, spec, location, "", qty, note)
    return {"ok": True}

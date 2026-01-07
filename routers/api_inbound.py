from fastapi import APIRouter, Form, HTTPException
from app.db import upsert_inventory, add_history
from app.utils.qr_format import build_item_qr

router = APIRouter(prefix="/api/inbound", tags=["api-inbound"])

@router.post("")
def inbound(
    warehouse: str = Form(...),
    operator: str = Form(""),
    brand: str = Form(...),
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
    upsert_inventory(warehouse, location, brand, item_code, item_name, lot, spec, qty, note)
    add_history("입고", warehouse, operator, brand, item_code, item_name, lot, spec, "", location, qty, note)
    return {"ok": True, "qr": build_item_qr(item_code, item_name, lot, spec, brand=brand)}

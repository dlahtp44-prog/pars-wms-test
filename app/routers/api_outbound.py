from fastapi import APIRouter, Form, HTTPException
from ..db import get_db
from .api_inventory import upsert_inventory, add_history

router = APIRouter(prefix="/api/outbound", tags=["outbound"])

@router.post("")
def outbound(
    warehouse: str = Form(...),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(""),
    spec: str = Form(""),
    qty: int = Form(...),
    note: str = Form(""),
    operator: str = Form("")
):
    if qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")
    with get_db() as conn:
        new_qty = upsert_inventory(
            conn,
            warehouse=warehouse.strip(),
            location=location.strip(),
            brand=brand.strip(),
            item_code=item_code.strip(),
            item_name=item_name.strip(),
            lot=lot.strip(),
            spec=spec.strip(),
            delta_qty=-qty,
            note=note.strip(),
        )
        add_history(
            conn,
            type="OUTBOUND",
            warehouse=warehouse,
            location=location,
            brand=brand,
            item_code=item_code,
            item_name=item_name,
            lot=lot,
            spec=spec,
            qty=qty,
            note=note,
            operator=operator
        )
    return {"ok": True, "new_qty": new_qty}

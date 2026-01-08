from fastapi import APIRouter, Form, HTTPException
from app.db import upsert_inventory, add_history

router = APIRouter(prefix="/api/outbound", tags=["출고"])

@router.post("")
def outbound(
    warehouse: str = Form(...),
    from_location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: float = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    if qty <= 0:
        raise HTTPException(400, "출고 수량은 1 이상이어야 합니다.")

    ok = upsert_inventory(
        warehouse=warehouse,
        location=from_location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty_delta=-qty,
        note=note or "출고",
    )
    if not ok:
        raise HTTPException(400, "재고 부족")

    add_history(
        type="출고",
        warehouse=warehouse,
        operator=operator,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        from_location=from_location,
        to_location="",
        qty=qty,
        note=note or "출고",
    )

    return {"ok": True}

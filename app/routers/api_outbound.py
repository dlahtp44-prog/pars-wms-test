from fastapi import APIRouter, Form, HTTPException
from app.db import upsert_inventory, add_history

router = APIRouter(prefix="/api/outbound", tags=["출고"])

@router.post("")
def outbound(
    warehouse: str = Form(...),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(""),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: float = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    # 1️⃣ 재고 차감
    ok = upsert_inventory(
        warehouse=warehouse,
        location=location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty_delta=-qty,
        note=note,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="재고 부족")

    # 2️⃣ 이력 기록
    add_history(
        type="출고",
        warehouse=warehouse,
        operator=operator,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        from_location=location,
        to_location="",
        qty=qty,
        note=note,
    )

    return {"ok": True}

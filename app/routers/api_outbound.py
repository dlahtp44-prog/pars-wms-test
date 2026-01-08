from fastapi import APIRouter, Form, HTTPException
from app.db import (
    upsert_inventory,
    add_history,
    resolve_inventory_brand_and_name,
)

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
    # 0️⃣ 브랜드 / 품명 자동 보정
    try:
        brand, resolved_item_name = resolve_inventory_brand_and_name(
            warehouse=warehouse,
            location=location,
            item_code=item_code,
            lot=lot,
            spec=spec,
            brand=brand,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not item_name:
        item_name = resolved_item_name

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
        note=note or "출고",
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
        note=note or "출고",
    )

    return {"ok": True}

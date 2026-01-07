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
    # -----------------------------
    # validation
    # -----------------------------
    if qty is None or str(qty).strip() == "":
        raise HTTPException(status_code=400, detail="수량은 필수입니다.")

    qty = int(qty)
    if qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")

    # -----------------------------
    # inventory
    # -----------------------------
    upsert_inventory(
        warehouse=warehouse,
        location=location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty_delta=qty,
        note=note
    )

    # -----------------------------
    # history
    # -----------------------------
    add_history(
        type="입고",
        warehouse=warehouse,
        operator=operator,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty=qty,
        from_location="",
        to_location=location,
        note=note
    )

    # -----------------------------
    # QR
    # -----------------------------
    return {
        "ok": True,
        "qr": build_item_qr(
            item_code=item_code,
            item_name=item_name,
            lot=lot,
            spec=spec,
            brand=brand
        )
    }

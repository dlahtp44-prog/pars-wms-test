from fastapi import APIRouter, Form, HTTPException
from ..db import get_db
from .api_inventory import upsert_inventory, add_history

router = APIRouter(prefix="/api/move", tags=["move"])

@router.post("")
def move(
    warehouse: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
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
    if from_location.strip() == to_location.strip():
        raise HTTPException(status_code=400, detail="출발/도착 로케이션이 같습니다.")
    with get_db() as conn:
        # 출발 차감
        upsert_inventory(
            conn,
            warehouse=warehouse.strip(),
            location=from_location.strip(),
            brand=brand.strip(),
            item_code=item_code.strip(),
            item_name=item_name.strip(),
            lot=lot.strip(),
            spec=spec.strip(),
            delta_qty=-qty,
            note=note.strip(),
        )
        # 도착 증가
        new_to_qty = upsert_inventory(
            conn,
            warehouse=warehouse.strip(),
            location=to_location.strip(),
            brand=brand.strip(),
            item_code=item_code.strip(),
            item_name=item_name.strip(),
            lot=lot.strip(),
            spec=spec.strip(),
            delta_qty=qty,
            note=note.strip(),
        )
        add_history(
            conn,
            type="MOVE",
            warehouse=warehouse,
            from_location=from_location,
            to_location=to_location,
            brand=brand,
            item_code=item_code,
            item_name=item_name,
            lot=lot,
            spec=spec,
            qty=qty,
            note=note,
            operator=operator
        )
    return {"ok": True, "to_new_qty": new_to_qty}

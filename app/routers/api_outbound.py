from fastapi import APIRouter, Form, HTTPException
from app.db import upsert_inventory

router = APIRouter(prefix="/api/outbound", tags=["Outbound"])


@router.post("")
def outbound(
    warehouse: str = Form(...),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: int = Form(...),
    note: str = Form(""),
):
    if qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")

    try:
        # 출고는 음수 처리
        upsert_inventory(
            warehouse,
            location,
            brand,
            item_code,
            item_name,
            lot,
            spec,
            -qty,
            note,
        )
    except ValueError as e:
        # ✅ 재고 부족 등 비즈니스 에러 처리
        raise HTTPException(status_code=400, detail=str(e))

    return {"result": "OK"}

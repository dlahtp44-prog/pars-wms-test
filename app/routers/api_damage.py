from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from app.db import add_damage_history, upsert_inventory

router = APIRouter(prefix="/api/damage", tags=["api-damage"])


@router.post("")
def create_damage(
    occurred_at: str = Form(...),
    warehouse: str = Form(...),
    location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: int = Form(...),
    damage_code_id: int = Form(...),
    detail: str = Form(""),
    deduct_inventory: str | None = Form(None),  # ← 옵션
):
    qty = int(qty)

    # -----------------------------
    # CS 이력 저장
    # -----------------------------
    add_damage_history(
        occurred_at=occurred_at,
        warehouse=warehouse,
        location=location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty=qty,
        damage_code_id=damage_code_id,
        detail=detail,
    )

    # -----------------------------
    # ✅ 재고 차감 (옵션)
    # -----------------------------
    if deduct_inventory == "1":
        upsert_inventory(
            warehouse=warehouse,
            location=location,
            brand=brand,
            item_code=item_code,
            item_name=item_name,
            lot=lot,
            spec=spec,
            qty_delta=-qty,
            note=f"CS 차감: {detail}"
        )

    # 완료 후 CS 이력으로 이동
    return RedirectResponse(
        url="/page/damage-history",
        status_code=303
    )

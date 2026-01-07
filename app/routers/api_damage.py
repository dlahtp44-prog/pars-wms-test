from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.db import add_damage_history

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
):
    """
    CS / 파손 등록
    - 재고 차감 없음
    - damage_history 테이블에만 기록
    """
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

    # 등록 후 CS 현황 페이지로 이동
    return RedirectResponse(
        url="/page/damage-history",
        status_code=HTTP_303_SEE_OTHER
    )

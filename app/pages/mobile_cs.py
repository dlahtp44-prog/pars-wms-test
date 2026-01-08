from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import date

from app.core.paths import TEMPLATES_DIR
from app.db import list_damage_codes
from app.utils.qr_format import is_item_qr, extract_item_fields

router = APIRouter(prefix="/m/cs", tags=["mobile-cs"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def mobile_cs_page(
    request: Request,
    qr: str = "",          # QR 스캔 결과
    warehouse: str = "",
    location: str = "",
):
    # 기본값
    item_code = ""
    item_name = ""
    lot = ""
    spec = ""
    brand = ""

    # ✅ ITEM QR일 때만 파싱
    if qr and is_item_qr(qr):
        try:
            item_code, item_name, lot, spec = extract_item_fields(qr)
        except Exception:
            # 잘못된 QR → 품목 정보 없이 CS 화면 진입
            pass

    damage_codes = list_damage_codes(active_only=True)

    return templates.TemplateResponse(
        "mobile_cs.html",
        {
            "request": request,
            "today": date.today().isoformat(),
            "warehouse": warehouse,
            "location": location,
            "brand": brand,
            "item_code": item_code,
            "item_name": item_name,
            "lot": lot,
            "spec": spec,
            "damage_codes": damage_codes,
        },
    )

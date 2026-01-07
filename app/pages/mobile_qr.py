from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory
from app.utils.qr_format import extract_location_only

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/m/qr", tags=["mobile-qr"])


# =========================
# QR 홈 (카메라 화면)
# =========================
@router.get("", response_class=HTMLResponse)
def qr_home(request: Request):
    return templates.TemplateResponse(
        "mobile/qr.html",
        {"request": request}
    )


# =========================
# 로케이션 QR → 재고 조회
# =========================
@router.get("/inventory", response_class=HTMLResponse)
def qr_inventory(request: Request, qrtext: str):
    # 🔑 반드시 로케이션만 추출
    location = extract_location_only(qrtext)

    rows = query_inventory(location=location)
    rows = [r for r in rows if int(r.get("qty", 0) or 0) > 0]

    return templates.TemplateResponse(
        "mobile/qr_inventory.html",
        {
            "request": request,
            "location": location,
            "items": rows,
        },
    )

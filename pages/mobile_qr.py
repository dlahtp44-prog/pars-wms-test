from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory
from app.utils.qr_format import extract_location_only

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/m", tags=["Mobile QR"])

# =========================
# 📱 QR 스캔 홈
# =========================
@router.get("/qr", response_class=HTMLResponse)
def qr_home(request: Request):
    return templates.TemplateResponse("m/qr.html", {"request": request})

# =========================
# 📦 로케이션 QR → 재고 조회
# =========================
@router.get("/qr/inventory", response_class=HTMLResponse)
def qr_inventory(request: Request, qrtext: str = Query("")):
    location = extract_location_only(qrtext)

    if not location:
        return templates.TemplateResponse(
            "m/qr_inventory.html",
            {"request": request, "location": "", "rows": [], "error": "로케이션 QR만 조회할 수 있습니다."},
        )

    rows = query_inventory(location=location)
    rows = [r for r in rows if int(r.get("qty", 0) or 0) > 0]

    return templates.TemplateResponse(
        "m/qr_inventory.html",
        {"request": request, "location": location, "rows": rows, "error": None},
    )

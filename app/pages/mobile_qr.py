from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory
from app.utils.qr_format import extract_location_only

router = APIRouter(prefix="/m/qr", tags=["mobile-qr"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def qr_home(request: Request):
    return templates.TemplateResponse("mobile/qr.html", {"request": request})


@router.get("/inventory", response_class=HTMLResponse)
def qr_inventory(request: Request, qrtext: str):
    """
    QR 재고 조회
    - 로케이션 QR만 허용
    """
    location = extract_location_only(qrtext or "")

    if not location:
        return templates.TemplateResponse(
            "mobile/qr_inventory.html",
            {"request": request, "location": "", "items": []},
        )

    rows = query_inventory(location=location)

    return templates.TemplateResponse(
        "mobile/qr_inventory.html",
        {
            "request": request,
            "location": location,
            "items": rows,
        },
    )

from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.core.paths import TEMPLATES_DIR
from app.db import get_db
from app.utils.qr_format import extract_location_only

router = APIRouter(prefix="/m/qr", tags=["Mobile QR"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# =========================
# 📱 QR 스캔 화면
# =========================
@router.get("", response_class=HTMLResponse)
def qr_home(request: Request):
    return templates.TemplateResponse(
        "mobile/qr.html",
        {"request": request}
    )


# =========================
# 📦 로케이션 재고 조회
# =========================
@router.get("/inventory", response_class=HTMLResponse)
def qr_inventory(
    request: Request,
    qrtext: str = Query("")
):
    # 🔒 qrtext 방어
    if not qrtext:
        return templates.TemplateResponse(
            "mobile/qr_inventory.html",
            {
                "request": request,
                "location": "",
                "items": [],
                "error": "QR 값이 전달되지 않았습니다."
            }
        )

    # 🔑 로케이션만 추출
    location = extract_location_only(qrtext)

    if not location:
        return templates.TemplateResponse(
            "mobile/qr_inventory.html",
            {
                "request": request,
                "location": "",
                "items": [],
                "error": "로케이션 QR만 조회할 수 있습니다."
            }
        )

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            brand,
            item_code,
            item_name,
            lot,
            spec,
            qty
        FROM inventory
        WHERE location = ?
          AND qty > 0
        ORDER BY item_code
    """, (location,))

    rows = cur.fetchall()

    items = [
        {
            "brand": r[0],
            "item_code": r[1],
            "item_name": r[2],
            "lot": r[3],
            "spec": r[4],
            "qty": r[5],
        }
        for r in rows
    ]

    return templates.TemplateResponse(
        "mobile/qr_inventory.html",
        {
            "request": request,
            "location": location,
            "items": items,
            "error": None
        }
    )

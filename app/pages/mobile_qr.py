# app/pages/mobile_qr.py

from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.db import get_db
from app.utils.qr_format import extract_location_only

router = APIRouter(prefix="/m/qr", tags=["mobile-qr"])
templates = Jinja2Templates(directory="templates")


# =========================
# 📱 QR 스캔 홈 (카메라)
# =========================
@router.get("", response_class=HTMLResponse)
def qr_home(request: Request):
    return templates.TemplateResponse(
        "mobile/qr.html",
        {"request": request}
    )


# =========================
# 📦 QR 재고 조회 결과
# =========================
@router.get("/inventory", response_class=HTMLResponse)
def qr_inventory(
    request: Request,
    qrtext: str = Query("")
):
    location = extract_location_only(qrtext or "")

    # 🔒 방어코드 (500 방지)
    if not location:
        return templates.TemplateResponse(
            "mobile/qr_inventory.html",
            {
                "request": request,
                "location": "",
                "items": [],
                "error": "❌ 로케이션 QR만 조회할 수 있습니다."
            }
        )

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            warehouse,
            location,
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
            "warehouse": r[0],
            "location": r[1],
            "brand": r[2],
            "item_code": r[3],
            "item_name": r[4],
            "lot": r[5],
            "spec": r[6],
            "qty": r[7],
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

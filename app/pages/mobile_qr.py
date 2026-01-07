# app/pages/mobile_qr.py

from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from app.db import get_db
from app.utils.qr_format import extract_location_only

router = APIRouter(prefix="/m", tags=["Mobile QR"])
templates = Jinja2Templates(directory="templates")


# =========================
# 📱 QR 스캔 홈 (카메라 화면)
# URL: /m/qr
# =========================
@router.get("/qr")
def qr_home(request: Request):
    return templates.TemplateResponse(
        "mobile/qr.html",
        {"request": request}
    )


# =========================
# 📦 QR 재고 조회 결과
# URL: /m/qr/inventory?qrtext=...
# =========================
@router.get("/qr/inventory")
def qr_inventory(
    request: Request,
    qrtext: str = Query(...)
):
    # 🔑 로케이션만 추출 (ITEM QR 완전 차단)
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

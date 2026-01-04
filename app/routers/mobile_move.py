from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import requests

from app.core.paths import TEMPLATES_DIR
from app.db import get_db

router = APIRouter(prefix="/m/move", tags=["mobile-move"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# =========================
# 1️⃣ 출발 로케이션 재고 조회
# =========================
@router.get("", response_class=HTMLResponse)
def move_from_location(request: Request, location: str = ""):
    items = []

    if location:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, item_code, item_name, lot, spec, qty
            FROM inventory
            WHERE location = ?
            ORDER BY item_name
        """, (location,))
        items = cur.fetchall()
        conn.close()

    return templates.TemplateResponse(
        "m/move_from.html",
        {
            "request": request,
            "location": location,
            "items": items,
        },
    )


# =========================
# 2️⃣ 이동 수량 입력
# =========================
@router.post("/qty", response_class=HTMLResponse)
def move_qty(
    request: Request,
    from_location: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
):
    return templates.TemplateResponse(
        "m/move_qty.html",
        {
            "request": request,
            "from_location": from_location,
            "item_code": item_code,
            "item_name": item_name,
            "lot": lot,
            "spec": spec,
        },
    )


# =========================
# 3️⃣ 도착 로케이션 QR 대기
# =========================
@router.post("/to", response_class=HTMLResponse)
def move_to_location(
    request: Request,
    from_location: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: int = Form(...),
):
    return templates.TemplateResponse(
        "m/move_to.html",
        {
            "request": request,
            "from_location": from_location,
            "item_code": item_code,
            "item_name": item_name,
            "lot": lot,
            "spec": spec,
            "qty": qty,
        },
    )


# =========================
# 4️⃣ 이동 완료
# =========================
@router.post("/done")
def move_done(
    from_location: str = Form(...),
    to_location: str = Form(...),
    item_code: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: int = Form(...),
):
    # 내부 API 호출
    requests.post(
        "http://localhost:8080/api/move",
        json={
            "from_location": from_location,
            "to_location": to_location,
            "item_code": item_code,
            "lot": lot,
            "spec": spec,
            "qty": qty,
        },
        timeout=5,
    )

    return RedirectResponse("/m", status_code=302)

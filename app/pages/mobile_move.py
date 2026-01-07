from urllib.parse import urlencode

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory, upsert_inventory, add_history
from app.utils.qr_format import extract_location_only

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/m/move", tags=["mobile-move"])


# =========================
# 시작 화면
# =========================
@router.get("", response_class=HTMLResponse)
def start(request: Request):
    return templates.TemplateResponse("m/move_start.html", {"request": request})


# =========================
# 1) 출발 로케이션 스캔
# =========================
@router.get("/from", response_class=HTMLResponse)
def from_scan(request: Request):
    return templates.TemplateResponse(
        "m/qr_scan.html",
        {
            "request": request,
            "title": "출발 로케이션 스캔",
            "desc": "출발 로케이션 QR을 스캔하세요.",
            "action": "/m/move/from/submit",
            "hidden": {},
        },
    )


@router.post("/from/submit")
def from_submit(qrtext: str = Form(...)):
    # 🔑 핵심: QR 문자열에서 로케이션만 추출
    from_location = extract_location_only(qrtext or "")
    return RedirectResponse(
        url=f"/m/move/select?from_location={from_location}",
        status_code=303,
    )


# =========================
# 2) 제품 선택 + 수량 입력
# =========================
@router.get("/select", response_class=HTMLResponse)
def select_item(request: Request, from_location: str):
    # 🔑 URL로 넘어온 값도 다시 정규화
    from_location = extract_location_only(from_location or "")

    rows = query_inventory(location=from_location)
    # 수량 있는 것만
    rows = [r for r in rows if int(r.get("qty", 0) or 0) > 0]

    return templates.TemplateResponse(
        "m/move_select.html",
        {
            "request": request,
            "from_location": from_location,
            "rows": rows,
        },
    )


@router.post("/select/submit")
def select_submit(
    from_location: str = Form(...),
    pick: str = Form(...),
    qty: int = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    from_location = extract_location_only(from_location or "")
    operator = (operator or "").strip()
    note = (note or "").strip()

    try:
        qty = int(qty)
    except:
        qty = 0

    if qty <= 0:
        return RedirectResponse(
            url=f"/m/move/select?from_location={from_location}",
            status_code=303,
        )

    # pick: warehouse|||brand|||item_code|||item_name|||lot|||spec
    parts = (pick or "").split("|||")
    if len(parts) != 6:
        return RedirectResponse(
            url=f"/m/move/select?from_location={from_location}",
            status_code=303,
        )

    warehouse, brand, item_code, item_name, lot, spec = [p.strip() for p in parts]

    # 현재 재고 확인
    rows = query_inventory(
        warehouse=warehouse,
        location=from_location,
        brand=brand,
        item_code=item_code,
        lot=lot,
        spec=spec,
    )
    available = int(rows[0].get("qty", 0)) if rows else 0

    if qty > available:
        return RedirectResponse(
            url=f"/m/move/select?from_location={from_location}",
            status_code=303,
        )

    params = {
        "warehouse": warehouse,
        "from_location": from_location,
        "brand": brand,
        "item_code": item_code,
        "item_name": item_name,
        "lot": lot,
        "spec": spec,
        "qty": qty,
        "operator": operator,
        "note": note,
    }

    return RedirectResponse(
        url=f"/m/move/to?{urlencode(params)}",
        status_code=303,
    )


# =========================
# 3) 도착 로케이션 스캔
# =========================
@router.get("/to", response_class=HTMLResponse)
def to_scan(
    request: Request,
    warehouse: str,
    from_location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    qty: int,
    operator: str = "",
    note: str = "",
):
    hidden = {
        "warehouse": warehouse,
        "from_location": extract_location_only(from_location or ""),
        "brand": brand or "",
        "item_code": item_code or "",
        "item_name": item_name or "",
        "lot": lot or "",
        "spec": spec or "",
        "qty": str(qty),
        "operator": operator or "",
        "note": note or "",
    }

    return templates.TemplateResponse(
        "m/qr_scan.html",
        {
            "request": request,
            "title": "도착 로케이션 스캔",
            "desc": "도착 로케이션 QR을 스캔하세요.",
            "action": "/m/move/to/submit",
            "hidden": hidden,
        },
    )


@router.post("/to/submit", response_class=HTMLResponse)
def to_submit(
    request: Request,
    qrtext: str = Form(...),
    warehouse: str = Form(..

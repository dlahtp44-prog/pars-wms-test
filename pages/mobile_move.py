from urllib.parse import urlencode

from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory, upsert_inventory, add_history
from app.utils.qr_format import extract_location_only

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/m", tags=["Mobile Move"])

# =========================
# 📦 이동 시작(안내)
# =========================
@router.get("/move", response_class=HTMLResponse)
def move_home(request: Request):
    return templates.TemplateResponse("m/move_start.html", {"request": request})

# =========================
# 1) 출발 로케이션 스캔
# =========================
@router.get("/move/from", response_class=HTMLResponse)
def move_from_scan(request: Request):
    return templates.TemplateResponse(
        "m/qr_scan.html",
        {"request": request, "title": "출발 로케이션 스캔", "action": "/m/move/from/submit", "hidden": {}, "error": None},
    )

@router.post("/move/from/submit")
def move_from_submit(qrtext: str = Form("")):
    from_location = extract_location_only(qrtext)
    if not from_location:
        return RedirectResponse(url="/m/move/from?err=1", status_code=303)
    return RedirectResponse(url=f"/m/move/select?from_location={from_location}", status_code=303)

# =========================
# 2) 출발 로케이션 재고 → 품목 선택
# =========================
@router.get("/move/select", response_class=HTMLResponse)
def move_select(request: Request, from_location: str = Query("")):
    if not from_location:
        return RedirectResponse(url="/m/move/from", status_code=303)

    rows = query_inventory(location=from_location)
    rows = [r for r in rows if int(r.get("qty", 0) or 0) > 0]

    return templates.TemplateResponse(
        "m/move_select.html",
        {"request": request, "from_location": from_location, "rows": rows},
    )

@router.post("/move/select/submit")
def move_select_submit(
    warehouse: str = Form(""),
    from_location: str = Form(""),
    brand: str = Form(""),
    item_code: str = Form(""),
    item_name: str = Form(""),
    lot: str = Form(""),
    spec: str = Form(""),
    qty: int = Form(0),
    move_qty: int = Form(0),
    operator: str = Form(""),
    note: str = Form(""),
):
    # 기본 검증
    if not from_location or not item_code or move_qty <= 0:
        return RedirectResponse(url=f"/m/move/select?from_location={from_location}", status_code=303)
    if move_qty > int(qty or 0):
        return RedirectResponse(url=f"/m/move/select?from_location={from_location}", status_code=303)

    params = {
        "warehouse": warehouse,
        "from_location": from_location,
        "brand": brand,
        "item_code": item_code,
        "item_name": item_name,
        "lot": lot,
        "spec": spec,
        "qty": str(qty),
        "move_qty": str(move_qty),
        "operator": operator,
        "note": note,
    }
    return RedirectResponse(url=f"/m/move/to?{urlencode(params)}", status_code=303)

# =========================
# 3) 도착 로케이션 스캔
# =========================
@router.get("/move/to", response_class=HTMLResponse)
def move_to_scan(
    request: Request,
    warehouse: str = Query(""),
    from_location: str = Query(""),
    brand: str = Query(""),
    item_code: str = Query(""),
    item_name: str = Query(""),
    lot: str = Query(""),
    spec: str = Query(""),
    qty: int = Query(0),
    move_qty: int = Query(0),
    operator: str = Query(""),
    note: str = Query(""),
):
    hidden = {
        "warehouse": warehouse,
        "from_location": from_location,
        "brand": brand,
        "item_code": item_code,
        "item_name": item_name,
        "lot": lot,
        "spec": spec,
        "qty": str(qty),
        "move_qty": str(move_qty),
        "operator": operator,
        "note": note,
    }
    return templates.TemplateResponse(
        "m/qr_scan.html",
        {"request": request, "title": "도착 로케이션 스캔", "action": "/m/move/to/submit", "hidden": hidden, "error": None},
    )

@router.post("/move/to/submit", response_class=HTMLResponse)
def move_to_submit(
    request: Request,
    qrtext: str = Form(""),  # 스캔 값
    warehouse: str = Form(""),
    from_location: str = Form(""),
    brand: str = Form(""),
    item_code: str = Form(""),
    item_name: str = Form(""),
    lot: str = Form(""),
    spec: str = Form(""),
    qty: int = Form(0),
    move_qty: int = Form(0),
    operator: str = Form(""),
    note: str = Form(""),
):
    to_location = extract_location_only(qrtext)

    if not to_location:
        hidden = {
            "warehouse": warehouse,
            "from_location": from_location,
            "brand": brand,
            "item_code": item_code,
            "item_name": item_name,
            "lot": lot,
            "spec": spec,
            "qty": str(qty),
            "move_qty": str(move_qty),
            "operator": operator,
            "note": note,
        }
        return templates.TemplateResponse(
            "m/qr_scan.html",
            {"request": request, "title": "도착 로케이션 스캔", "action": "/m/move/to/submit", "hidden": hidden, "error": "로케이션 QR만 허용됩니다."},
        )

    # 이동 처리
    # 출발 차감
    upsert_inventory(
        warehouse=warehouse,
        location=from_location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty_delta=-int(move_qty or 0),
    )
    # 도착 가산
    upsert_inventory(
        warehouse=warehouse,
        location=to_location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty_delta=int(move_qty or 0),
    )

    add_history(
        type_="MOVE",
        warehouse=warehouse,
        location=from_location,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        qty=int(move_qty or 0),
        operator=operator,
        note=f"FROM:{from_location} -> TO:{to_location} {note}".strip(),
    )

    msg = (
        f"[MOVE] {item_code} / {item_name}\n"
        f"LOT:{lot} / 규격:{spec}\n"
        f"{from_location} -> {to_location} / 수량:{move_qty}"
    )

    return templates.TemplateResponse(
        "m/move_done.html",
        {"request": request, "msg": msg, "to_location": to_location},
    )

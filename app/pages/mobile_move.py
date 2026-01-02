from urllib.parse import urlencode

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory, get_inventory_qty, upsert_inventory, add_history

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/m/move", tags=["mobile-move"])

@router.get("", response_class=HTMLResponse)
def start(request: Request):
    return templates.TemplateResponse("m/move_start.html", {"request": request})

@router.get("/from", response_class=HTMLResponse)
def scan_from(request: Request):
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
    from_location = (qrtext or "").strip()
    return RedirectResponse(url=f"/m/move/select?from_location={from_location}", status_code=303)

@router.get("/select", response_class=HTMLResponse)
def select_item(request: Request, from_location: str, err: str = ""):
    rows = query_inventory(location=from_location)
    return templates.TemplateResponse(
        "m/move_select.html",
        {"request": request, "from_location": from_location, "rows": rows, "err": err},
    )

@router.post("/select/submit")
def select_submit(
    from_location: str = Form(...),
    picked: str = Form(...),
    qty: int = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    parts = picked.split("||")
    warehouse, brand, item_code, item_name, lot, spec = (parts + [""] * 6)[:6]

    # 재고 부족 사전 차단 (서버측)
    available = get_inventory_qty(warehouse, from_location, item_code, lot, spec)
    if int(qty) <= 0:
        return RedirectResponse(url=f"/m/move/select?from_location={from_location}", status_code=303)
    if available < int(qty):
        # select 화면으로 다시 보내며 쿼리로 에러 메시지 전달
        qs_err = urlencode({"from_location": from_location, "err": f"재고 부족: 현재 {available} / 요청 {qty}"})
        return RedirectResponse(url=f"/m/move/select?{qs_err}", status_code=303)
    qs = urlencode(
        {
            "warehouse": warehouse,
            "from_location": from_location,
            "brand": brand,
            "item_code": item_code,
            "item_name": item_name,
            "lot": lot,
            "spec": spec,
            "qty": str(qty),
            "operator": operator or "",
            "note": note,
        }
    )
    return RedirectResponse(url=f"/m/move/to?{qs}", status_code=303)

@router.get("/to", response_class=HTMLResponse)
def scan_to(
    request: Request,
    warehouse: str,
    from_location: str,
    operator: str = "",
    brand: str = "",
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    qty: int,
    note: str = "",
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
    warehouse: str = Form(...),
    from_location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: int = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    to_location = (qrtext or "").strip()

    if int(qty) <= 0:
        msg = "ERROR\n- 수량은 1 이상이어야 합니다.\n"
        return templates.TemplateResponse(
            "m/move_done.html",
            {"request": request, "msg": msg, "to_location": to_location},
        )

    # 최종 차단 (출발지 재고 재확인)
    available = get_inventory_qty(warehouse, from_location, item_code, lot, spec)
    if available < int(qty):
        msg = f"ERROR\n- 출발 로케이션 재고 부족\n- 현재: {available}\n- 요청: {qty}\n"
        return templates.TemplateResponse(
            "m/move_done.html",
            {"request": request, "msg": msg, "to_location": to_location},
        )

    # 이동 처리(출발 - / 도착 +)
    upsert_inventory(warehouse, from_location, brand, item_code, item_name, lot, spec, -int(qty), note)
    upsert_inventory(warehouse, to_location, brand, item_code, item_name, lot, spec, int(qty), note)
    add_history("이동", warehouse, operator, brand, item_code, item_name, lot, spec, from_location, to_location, int(qty), note)

    msg = (
        f"OK\n"
        f"- 창고: {warehouse}\n"
        f"- 출발: {from_location}\n"
        f"- 도착: {to_location}\n"
        f"- 브랜드: {brand}\n"
        f"- 품번: {item_code}\n"
        f"- LOT: {lot}\n"
        f"- 규격: {spec}\n"
        f"- 수량: {qty}\n"
    )
    return templates.TemplateResponse(
        "m/move_done.html",
        {"request": request, "msg": msg, "to_location": to_location},
    )

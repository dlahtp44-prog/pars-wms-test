from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory, upsert_inventory, add_history
from app.utils.qr_format import detect_qr_type, extract_location, parse_qr

router = APIRouter(prefix="/m/move", tags=["mobile-move"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# =========================
# A. 기존 3단계 이동 (안정)
# =========================

@router.get("", response_class=HTMLResponse)
def move_home(request: Request):
    return templates.TemplateResponse("m/move_home.html", {"request": request})


@router.get("/from", response_class=HTMLResponse)
def move_from(request: Request, error: str = ""):
    return templates.TemplateResponse("m/move_from.html", {"request": request, "error": error})


@router.post("/from/submit")
def move_from_submit(qrtext: str = Form(...)):
    raw = (qrtext or "").strip()

    if detect_qr_type(raw) == "ITEM":
        return RedirectResponse(
            url="/m/move/from?error=출발 로케이션 QR을 스캔하세요.",
            status_code=303
        )

    loc = extract_location(raw)
    if not loc:
        return RedirectResponse(
            url="/m/move/from?error=로케이션 인식 실패",
            status_code=303
        )

    return RedirectResponse(
        url=f"/m/move/select?from_location={loc}",
        status_code=303
    )


@router.get("/select", response_class=HTMLResponse)
def move_select(request: Request, from_location: str):
    rows = query_inventory(location=from_location)
    return templates.TemplateResponse(
        "m/move_select.html",
        {"request": request, "from_location": from_location, "rows": rows}
    )


@router.post("/select/submit")
def move_select_submit(
    warehouse: str = Form(...),
    from_location: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    available_qty: int = Form(...),
):
    return RedirectResponse(
        url=(
            "/m/move/to"
            f"?warehouse={warehouse}"
            f"&from_location={from_location}"
            f"&item_code={item_code}"
            f"&item_name={item_name}"
            f"&lot={lot}"
            f"&spec={spec}"
            f"&available_qty={available_qty}"
        ),
        status_code=303
    )


@router.get("/to", response_class=HTMLResponse)
def move_to(
    request: Request,
    warehouse: str,
    from_location: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    available_qty: int,
    error: str = "",
):
    return templates.TemplateResponse(
        "m/move_to.html",
        {
            "request": request,
            "warehouse": warehouse,
            "from_location": from_location,
            "item_code": item_code,
            "item_name": item_name,
            "lot": lot,
            "spec": spec,
            "available_qty": available_qty,
            "error": error,
        },
    )


@router.post("/to/submit")
def move_to_submit(
    warehouse: str = Form(...),
    from_location: str = Form(...),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    available_qty: int = Form(...),
    qty: int = Form(...),
    to_qr: str = Form(...),
    note: str = Form(""),
):
    raw = (to_qr or "").strip()

    if detect_qr_type(raw) == "ITEM":
        return RedirectResponse(
            url="/m/move/to?error=도착 로케이션 QR을 스캔하세요.",
            status_code=303
        )

    to_location = extract_location(raw)
    if not to_location:
        raise HTTPException(status_code=400, detail="도착 로케이션 인식 실패")

    if qty <= 0 or qty > available_qty:
        raise HTTPException(status_code=400, detail="수량 오류")

    upsert_inventory(warehouse, from_location, item_code, item_name, lot, spec, -qty, note)
    upsert_inventory(warehouse, to_location, item_code, item_name, lot, spec, qty, note)
    add_history("이동", warehouse, item_code, item_name, lot, spec, from_location, to_location, qty, note)

    return templates.TemplateResponse(
        "m/move_done.html",
        {
            "request": {},
            "warehouse": warehouse,
            "from_location": from_location,
            "to_location": to_location,
            "item_code": item_code,
            "item_name": item_name,
            "lot": lot,
            "spec": spec,
            "qty": qty,
        },
    )


# =========================
# B. ITEM QR 즉시 이동 (신규)
# =========================

@router.get("/item", response_class=HTMLResponse)
def move_item_qr(
    request: Request,
    qr: str,
    warehouse: str = "MAIN",
):
    parsed = parse_qr(qr)

    item_code = parsed.get("item_code")
    lot = parsed.get("lot")

    if not item_code or not lot:
        raise HTTPException(status_code=400, detail="ITEM QR 인식 실패")

    return templates.TemplateResponse(
        "m/move_item.html",
        {
            "request": request,
            "warehouse": warehouse,
            "item_code": item_code,
            "lot": lot,
        }
    )

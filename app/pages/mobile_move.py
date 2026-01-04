from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory, upsert_inventory, add_history
from app.utils.qr_format import detect_qr_type, extract_location, extract_item_fields

router = APIRouter(prefix="/m/move", tags=["mobile-move"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def move_home(request: Request):
    return templates.TemplateResponse("m/move_home.html", {"request": request})


# -------------------------
# Step 1) FROM location scan
# -------------------------
@router.get("/from", response_class=HTMLResponse)
def move_from(request: Request, error: str = ""):
    return templates.TemplateResponse("m/move_from.html", {"request": request, "error": error})


@router.post("/from/submit")
def move_from_submit(qrtext: str = Form(...)):
    raw = (qrtext or "").strip()
    if detect_qr_type(raw) == "ITEM":
        return RedirectResponse(url="/m/move/from?error=출발 로케이션 QR을 스캔해 주세요.(품목 QR 아님)", status_code=303)

    loc = extract_location(raw) or raw
    if not loc:
        return RedirectResponse(url="/m/move/from?error=QR 값이 비어있습니다.", status_code=303)

    return RedirectResponse(url=f"/m/move/select?from_location={loc}", status_code=303)


# -------------------------
# Step 2) Select item from inventory at FROM
# -------------------------
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


# -------------------------
# Step 3) TO location scan + qty input
# -------------------------
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


@router.post("/to/submit", response_class=HTMLResponse)
def move_to_submit(
    request: Request,
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
        # 현장 실수 방지
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
                "&error=도착 로케이션 QR을 스캔해 주세요.(품목 QR 아님)"
            ),
            status_code=303,
        )

    to_location = extract_location(raw) or raw
    if not to_location:
        raise HTTPException(status_code=400, detail="도착 로케이션이 비어있습니다.")
    if qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")
    if qty > int(available_qty):
        raise HTTPException(status_code=400, detail="이동 수량이 현재고보다 큽니다.")

    # 재고 이동(빼기/더하기)
    upsert_inventory(warehouse, from_location, item_code, item_name, lot, spec, -qty, note)
    upsert_inventory(warehouse, to_location, item_code, item_name, lot, spec, qty, note)
    add_history("이동", warehouse, item_code, item_name, lot, spec, from_location, to_location, qty, note)

    return templates.TemplateResponse(
        "m/move_done.html",
        {
            "request": request,
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

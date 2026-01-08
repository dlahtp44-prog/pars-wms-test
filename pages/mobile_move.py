import re
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import query_inventory, upsert_inventory, add_history

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/m/move", tags=["모바일이동"])

_LOC_RE = re.compile(r"^[A-Za-z0-9\-_/]+$")

def _extract_location(raw: str) -> str:
    raw = (raw or "").strip()
    # QR이 URL쿼리 형태로 들어오는 경우 (type=...&location=... 또는 ...?location=...)
    if "location=" in raw:
        try:
            part = raw.split("location=", 1)[1]
            part = part.split("&", 1)[0]
            raw = part
        except Exception:
            pass
    # type=ITEM... 같은 쿼리스트링이 그대로 들어오면 차단
    if ("type=" in raw) or ("item_code=" in raw) or ("&" in raw) or ("=" in raw):
        return ""
    if not raw:
        return ""
    if len(raw) > 60:
        return ""
    if not _LOC_RE.match(raw):
        return ""
    return raw

@router.get("/start", response_class=HTMLResponse)
def start(request: Request):
    return templates.TemplateResponse("m/move_start.html", {"request": request})

@router.get("/select", response_class=HTMLResponse)
def select(request: Request, warehouse: str = "", from_location: str = ""):
    fl = _extract_location(from_location)
    if not fl:
        return templates.TemplateResponse(
            "m/move_select.html",
            {"request": request, "warehouse": warehouse, "from_location": "", "rows": [], "msg": "출발 로케이션 QR이 올바르지 않습니다."},
        )
    rows = query_inventory(warehouse=warehouse or None, location=fl, limit=200)
    return templates.TemplateResponse(
        "m/move_select.html",
        {"request": request, "warehouse": warehouse, "from_location": fl, "rows": rows, "msg": ""},
    )

@router.post("/do")
def do_move(
    warehouse: str = Form(...),
    operator: str = Form(""),
    from_location: str = Form(...),
    to_location: str = Form(...),
    brand: str = Form(""),
    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: float = Form(...),
    note: str = Form(""),
):
    fl = _extract_location(from_location)
    tl = _extract_location(to_location)
    if not fl or not tl:
        raise HTTPException(status_code=400, detail="로케이션 QR 값이 올바르지 않습니다.")
    if fl == tl:
        raise HTTPException(status_code=400, detail="출발/도착 로케이션이 동일합니다.")
    if qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")

    # 출발지 차감
    ok = upsert_inventory(warehouse, fl, brand, item_code, item_name, lot, spec, -qty, note or "이동 출발")
    if not ok:
        raise HTTPException(status_code=400, detail="재고 부족으로 이동할 수 없습니다.")
    # 도착지 증감
    upsert_inventory(warehouse, tl, brand, item_code, item_name, lot, spec, qty, note or "이동 도착")

    add_history(
        type="이동",
        warehouse=warehouse,
        operator=operator,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot=lot,
        spec=spec,
        from_location=fl,
        to_location=tl,
        qty=qty,
        note=note or "이동",
    )
    return RedirectResponse(url="/m/move/done", status_code=303)

@router.get("/done", response_class=HTMLResponse)
def done(request: Request):
    return templates.TemplateResponse("m/move_done.html", {"request": request})

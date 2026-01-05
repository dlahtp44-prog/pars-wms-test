from fastapi import APIRouter, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ..core.paths import TEMPLATES_DIR
from ..db import get_db

router = APIRouter(prefix="/m/move", tags=["mobile"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("", response_class=HTMLResponse)
def move_home(request: Request):
    return templates.TemplateResponse("m/move_home.html", {"request": request})

@router.get("/from", response_class=HTMLResponse)
def move_from(request: Request, warehouse: str = "MAIN", from_location: str | None = None):
    return templates.TemplateResponse("m/move_from.html", {"request": request, "warehouse": warehouse, "from_location": from_location or ""})

@router.get("/select", response_class=HTMLResponse)
def move_select(request: Request, warehouse: str, from_location: str):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM inventory WHERE warehouse=? AND location=? AND qty>0 ORDER BY item_code",
            (warehouse, from_location)
        ).fetchall()
    return templates.TemplateResponse("m/move_select.html", {"request": request, "warehouse": warehouse, "from_location": from_location, "rows": rows})

@router.post("/select")
def move_select_post(
    warehouse: str = Form(...),
    from_location: str = Form(...),
    item_code: str = Form(...),
    lot: str = Form(""),
    spec: str = Form("")
):
    # 다음 단계: 도착 QR 스캔 페이지로
    qs = f"warehouse={warehouse}&from_location={from_location}&item_code={item_code}&lot={lot}&spec={spec}"
    return RedirectResponse(url="/m/move/to?"+qs, status_code=302)

@router.get("/to", response_class=HTMLResponse)
def move_to(request: Request, warehouse: str, from_location: str, item_code: str, lot: str = "", spec: str = ""):
    # to_location은 스캔 후 submit에서 이동완료로 redirect
    return templates.TemplateResponse("m/move_to.html", {"request": request, "warehouse": warehouse, "from_location": from_location, "item_code": item_code, "lot": lot, "spec": spec})

@router.post("/do")
def move_do(
    warehouse: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
    item_code: str = Form(...),
    lot: str = Form(""),
    spec: str = Form(""),
    qty: int = Form(...),
):
    # item_name/brand는 inventory에서 조회
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?",
            (warehouse, from_location, item_code, lot, spec)
        ).fetchone()
        if not row:
            return RedirectResponse(url="/m/move", status_code=302)
        item_name=row["item_name"]
        brand=row["brand"]
        # 출발 차감
        conn.execute(
            "UPDATE inventory SET qty=qty-?, updated_at=datetime('now','localtime') WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?",
            (qty, warehouse, from_location, item_code, lot, spec)
        )
        # 도착 upsert
        existing = conn.execute(
            "SELECT qty FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?",
            (warehouse, to_location, item_code, lot, spec)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE inventory SET qty=qty+?, brand=?, item_name=?, updated_at=datetime('now','localtime') WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?",
                (qty, brand, item_name, warehouse, to_location, item_code, lot, spec)
            )
        else:
            conn.execute(
                "INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot, spec, qty, note, updated_at) VALUES (?,?,?,?,?,?,?,?,?,datetime('now','localtime'))",
                (warehouse, to_location, brand, item_code, item_name, lot, spec, qty, "",)
            )
        # history
        conn.execute(
            "INSERT INTO history (created_at, type, warehouse, location, from_location, to_location, brand, item_code, item_name, lot, spec, qty, note, operator) VALUES (datetime('now','localtime'),?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("MOVE", warehouse, "", from_location, to_location, brand, item_code, item_name, lot, spec, qty, "", "")
        )
    return RedirectResponse(url=f"/m/move/done?warehouse={warehouse}&from_location={from_location}&to_location={to_location}&item_code={item_code}&item_name={item_name}&lot={lot}&spec={spec}&qty={qty}", status_code=302)

@router.get("/done", response_class=HTMLResponse)
def move_done(request: Request, warehouse: str, from_location: str, to_location: str, item_code: str, item_name: str, lot: str = "", spec: str = "", qty: int = 0):
    return templates.TemplateResponse("m/move_done.html", {"request": request, "warehouse": warehouse, "from_location": from_location, "to_location": to_location, "item_code": item_code, "item_name": item_name, "lot": lot, "spec": spec, "qty": qty})

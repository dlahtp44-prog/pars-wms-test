from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import get_db

router = APIRouter(prefix="/m/move", tags=["mobile-move"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def move_page(
    request: Request,
    location: str = "",
):
    """
    출발 로케이션 기준 재고 목록 표시
    """
    items = []

    if location:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                item_code,
                item_name,
                lot,
                spec,
                qty
            FROM inventory
            WHERE location = ?
            ORDER BY item_code
        """, (location,))
        items = cur.fetchall()
        conn.close()

    return templates.TemplateResponse(
        "m/move.html",
        {
            "request": request,
            "location": location,
            "items": items,
        },
    )


@router.post("/submit")
def move_submit(
    from_location: str = Form(...),
    to_location: str = Form(...),
    item_code: str = Form(...),
    lot: str = Form(...),
    spec: str = Form(...),
    qty: int = Form(...),
):
    if qty <= 0:
        return {"error": "수량은 1 이상이어야 합니다."}

    conn = get_db()
    cur = conn.cursor()

    # FROM 재고 확인
    cur.execute("""
        SELECT id, qty
        FROM inventory
        WHERE location=? AND item_code=? AND lot=? AND spec=?
    """, (from_location, item_code, lot, spec))
    row = cur.fetchone()

    if not row:
        conn.close()
        return {"error": "출발 로케이션에 재고가 없습니다."}

    inv_id, current_qty = row
    if current_qty < qty:
        conn.close()
        return {"error": "재고 수량이 부족합니다."}

    # FROM 차감
    cur.execute(
        "UPDATE inventory SET qty = qty - ? WHERE id = ?",
        (qty, inv_id)
    )

    # TO 증가 또는 생성
    cur.execute("""
        SELECT id FROM inventory
        WHERE location=? AND item_code=? AND lot=? AND spec=?
    """, (to_location, item_code, lot, spec))
    to_row = cur.fetchone()

    if to_row:
        cur.execute(
            "UPDATE inventory SET qty = qty + ? WHERE id = ?",
            (qty, to_row[0])
        )
    else:
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, item_code, item_name, lot, spec, qty)
            SELECT warehouse, ?, item_code, item_name, lot, spec, ?
            FROM inventory WHERE id = ?
        """, (to_location, qty, inv_id))

    # 이력 기록
    cur.execute("""
        INSERT INTO history
        (type, warehouse, item_code, item_name, lot, spec, from_location, to_location, qty)
        SELECT
            'MOVE', warehouse, item_code, item_name, lot, spec, ?, ?, ?
        FROM inventory WHERE id = ?
    """, (from_location, to_location, qty, inv_id))

    conn.commit()
    conn.close()

    return {"result": "OK"}

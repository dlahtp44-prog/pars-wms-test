from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db

router = APIRouter(prefix="/m/move", tags=["mobile-move"])
templates = Jinja2Templates(directory="app/templates")


# ---------------------------
# 이동 화면 (제품 선택)
# ---------------------------
@router.get("", response_class=HTMLResponse)
def move_page(request: Request):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            warehouse,
            location,
            item_code,
            item_name,
            lot,
            size,
            quantity
        FROM inventory
        WHERE quantity > 0
        ORDER BY warehouse, location, item_code
    """)
    items = cur.fetchall()

    return templates.TemplateResponse(
        "mobile/move.html",
        {
            "request": request,
            "items": items
        }
    )


# ---------------------------
# 이동 처리 (서버 검증)
# ---------------------------
@router.post("/submit")
def move_submit(
    warehouse: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),

    item_code: str = Form(...),
    item_name: str = Form(...),
    lot: str = Form(...),
    size: str = Form(...),

    quantity: int = Form(...),
    worker: str | None = Form(None),   # 추후 로그인으로 대체
):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")

    conn = get_db()
    cur = conn.cursor()

    # 현재 재고 조회 (차감 기준)
    cur.execute("""
        SELECT quantity
        FROM inventory
        WHERE warehouse = ?
          AND location = ?
          AND item_code = ?
          AND item_name = ?
          AND lot = ?
          AND size = ?
    """, (
        warehouse,
        from_location,
        item_code,
        item_name,
        lot,
        size,
    ))

    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="해당 재고를 찾을 수 없습니다.")

    current_qty = row[0]
    if quantity > current_qty:
        raise HTTPException(
            status_code=400,
            detail=f"재고 부족 (현재 {current_qty})"
        )

    # 1️⃣ 출발지 차감
    cur.execute("""
        UPDATE inventory
        SET quantity = quantity - ?
        WHERE warehouse = ?
          AND location = ?
          AND item_code = ?
          AND item_name = ?
          AND lot = ?
          AND size = ?
    """, (
        quantity,
        warehouse,
        from_location,
        item_code,
        item_name,
        lot,
        size,
    ))

    # 2️⃣ 도착지 적재 (있으면 +, 없으면 insert)
    cur.execute("""
        SELECT quantity
        FROM inventory
        WHERE warehouse = ?
          AND location = ?
          AND item_code = ?
          AND item_name = ?
          AND lot = ?
          AND size = ?
    """, (
        warehouse,
        to_location,
        item_code,
        item_name,
        lot,
        size,
    ))

    dest = cur.fetchone()
    if dest:
        cur.execute("""
            UPDATE inventory
            SET quantity = quantity + ?
            WHERE warehouse = ?
              AND location = ?
              AND item_code = ?
              AND item_name = ?
              AND lot = ?
              AND size = ?
        """, (
            quantity,
            warehouse,
            to_location,
            item_code,
            item_name,
            lot,
            size,
        ))
    else:
        cur.execute("""
            INSERT INTO inventory (
                warehouse, location,
                item_code, item_name,
                lot, size,
                quantity
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            warehouse,
            to_location,
            item_code,
            item_name,
            lot,
            size,
            quantity,
        ))

    # 3️⃣ 이력 기록
    cur.execute("""
        INSERT INTO history (
            type,
            warehouse,
            from_location,
            to_location,
            item_code,
            item_name,
            lot,
            size,
            quantity,
            worker
        ) VALUES (
            'MOVE', ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, (
        warehouse,
        from_location,
        to_location,
        item_code,
        item_name,
        lot,
        size,
        quantity,
        worker,
    ))

    conn.commit()

    return RedirectResponse("/m", status_code=303)

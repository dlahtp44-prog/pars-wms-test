from fastapi import APIRouter, Form, HTTPException
from app.db import get_db

router = APIRouter(prefix="/api", tags=["move"])

@router.post("/move")
def move(
    warehouse: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
    item_code: str = Form(...),
    lot: str = Form(...),
    qty: int = Form(...),
    note: str = Form("")
):
    if qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")

    conn = get_db()
    cur = conn.cursor()

    # 출발지 차감
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot=?
    """, (qty, warehouse, from_location, item_code, lot))

    # 도착지 증가
    cur.execute("""
        INSERT INTO inventory (warehouse, location, item_code, lot, qty)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot)
        DO UPDATE SET qty = qty + excluded.qty
    """, (warehouse, to_location, item_code, lot, qty))

    # 이력 기록
    cur.execute("""
        INSERT INTO history
        (warehouse, from_location, to_location, item_code, lot, qty, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (warehouse, from_location, to_location, item_code, lot, qty, note))

    conn.commit()
    return {"status": "ok"}

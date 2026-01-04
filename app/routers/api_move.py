from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import get_db

router = APIRouter(prefix="/api/move", tags=["Move"])


class MoveRequest(BaseModel):
    from_location: str
    to_location: str
    item_code: str
    lot: str
    spec: str
    qty: int


@router.post("")
def move_inventory(req: MoveRequest):
    if req.qty <= 0:
        raise HTTPException(status_code=400, detail="수량은 1 이상이어야 합니다.")

    conn = get_db()
    cur = conn.cursor()

    # 1) FROM 재고 확인
    cur.execute("""
        SELECT id, qty
        FROM inventory
        WHERE location=? AND item_code=? AND lot=? AND spec=?
    """, (req.from_location, req.item_code, req.lot, req.spec))
    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="출발 로케이션에 재고가 없습니다.")

    inv_id, current_qty = row
    if current_qty < req.qty:
        raise HTTPException(status_code=400, detail="재고 수량 부족")

    # 2) FROM 차감
    cur.execute(
        "UPDATE inventory SET qty = qty - ? WHERE id = ?",
        (req.qty, inv_id)
    )

    # 3) TO 증가(없으면 생성)
    cur.execute("""
        SELECT id FROM inventory
        WHERE location=? AND item_code=? AND lot=? AND spec=?
    """, (req.to_location, req.item_code, req.lot, req.spec))
    to_row = cur.fetchone()

    if to_row:
        cur.execute(
            "UPDATE inventory SET qty = qty + ? WHERE id = ?",
            (req.qty, to_row[0])
        )
    else:
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, item_code, item_name, lot, spec, qty)
            SELECT warehouse, ?, item_code, item_name, lot, spec, ?
            FROM inventory WHERE id = ?
        """, (req.to_location, req.qty, inv_id))

    # 4) 이력 기록
    cur.execute("""
        INSERT INTO history
        (type, warehouse, item_code, item_name, lot, spec, from_location, to_location, qty)
        SELECT
            'MOVE', warehouse, item_code, item_name, lot, spec, ?, ?, ?
        FROM inventory WHERE id = ?
    """, (req.from_location, req.to_location, req.qty, inv_id))

    conn.commit()
    conn.close()

    return {"result": "OK"}

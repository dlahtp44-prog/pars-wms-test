from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import get_db

router = APIRouter(prefix="/api/move", tags=["Move"])


class MoveRequest(BaseModel):
    warehouse: str
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

    try:
        # 1️⃣ FROM 재고 확인 (warehouse 포함)
        cur.execute("""
            SELECT id, qty, item_name
            FROM inventory
            WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?
        """, (
            req.warehouse,
            req.from_location,
            req.item_code,
            req.lot,
            req.spec,
        ))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="출발 로케이션에 재고가 없습니다.")

        inv_id, current_qty, item_name = row

        if current_qty < req.qty:
            raise HTTPException(status_code=400, detail="재고 수량 부족")

        # 2️⃣ FROM 차감
        new_qty = current_qty - req.qty
        if new_qty > 0:
            cur.execute(
                "UPDATE inventory SET qty=? WHERE id=?",
                (new_qty, inv_id)
            )
        else:
            # 수량 0 → row 삭제
            cur.execute("DELETE FROM inventory WHERE id=?", (inv_id,))

        # 3️⃣ TO 증가 or 생성
        cur.execute("""
            SELECT id FROM inventory
            WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?
        """, (
            req.warehouse,
            req.to_location,
            req.item_code,
            req.lot,
            req.spec,
        ))
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
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                req.warehouse,
                req.to_location,
                req.item_code,
                item_name,
                req.lot,
                req.spec,
                req.qty,
            ))

        # 4️⃣ 이력 기록
        cur.execute("""
            INSERT INTO history
            (type, warehouse, item_code, item_name, lot, spec,
             from_location, to_location, qty)
            VALUES
            ('MOVE', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            req.warehouse,
            req.item_code,
            item_name,
            req.lot,
            req.spec,
            req.from_location,
            req.to_location,
            req.qty,
        ))

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.close()

    return {
        "result": "OK",
        "message": "재고 이동 완료",
        "data": {
            "warehouse": req.warehouse,
            "item_code": req.item_code,
            "lot": req.lot,
            "spec": req.spec,
            "qty": req.qty,
            "from": req.from_location,
            "to": req.to_location,
        }
    }

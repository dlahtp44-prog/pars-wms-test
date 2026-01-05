from fastapi import APIRouter, Form, HTTPException
from datetime import datetime
from ..db import get_db

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@router.get("")
def get_memo(date: str):
    # date: YYYY-MM-DD
    with get_db() as conn:
        row = conn.execute("SELECT date, memo, updated_at FROM calendar_memo WHERE date=?", (date,)).fetchone()
        return {"date": date, "memo": (row["memo"] if row else ""), "updated_at": (row["updated_at"] if row else "")}

@router.post("/save")
def save_memo(date: str = Form(...), memo: str = Form("")):
    date = date.strip()
    if not date or len(date) != 10:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).")
    with get_db() as conn:
        conn.execute(
            "INSERT INTO calendar_memo (date, memo, updated_at) VALUES (?,?,?) "
            "ON CONFLICT(date) DO UPDATE SET memo=excluded.memo, updated_at=excluded.updated_at",
            (date, memo, _now())
        )
    return {"ok": True}

@router.post("/delete")
def delete_memo(date: str = Form(...)):
    with get_db() as conn:
        conn.execute("DELETE FROM calendar_memo WHERE date=?", (date.strip(),))
    return {"ok": True}

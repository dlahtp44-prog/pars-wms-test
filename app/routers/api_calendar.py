from fastapi import APIRouter, Form
from datetime import datetime
from app.db import db
router=APIRouter(prefix="/api/calendar", tags=["calendar"])
@router.post("/save")
def save(memo_date:str=Form(...), memo:str=Form(...)):
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db() as conn:
        conn.execute("INSERT INTO calendar_memo(memo_date,memo,updated_at) VALUES(?,?,?) ON CONFLICT(memo_date) DO UPDATE SET memo=excluded.memo, updated_at=excluded.updated_at",
                     (memo_date,memo,now))
    return {"ok":True}
@router.post("/delete")
def delete(memo_date:str=Form(...)):
    with db() as conn:
        conn.execute("DELETE FROM calendar_memo WHERE memo_date=?",(memo_date,))
    return {"ok":True}

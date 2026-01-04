from fastapi import APIRouter
from pydantic import BaseModel
from app.db import get_calendar_month, save_calendar_memo

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

class SaveMemo(BaseModel):
    memo_date: str   # YYYY-MM-DD
    memo_text: str = ""

@router.get("/month")
def month(year: int, month: int):
    return {"year": year, "month": month, "memos": get_calendar_month(year, month)}

@router.post("/save")
def save(payload: SaveMemo):
    return save_calendar_memo(payload.memo_date, payload.memo_text)

from fastapi import APIRouter, Form, HTTPException, Query
from app.db import upsert_calendar_memo, get_calendar_memos_for_month

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/month")
def month(year: int = Query(..., ge=2000, le=2100), month: int = Query(..., ge=1, le=12)):
    # returns { "YYYY-MM-DD": {memo, author, updated_at}, ... }
    return get_calendar_memos_for_month(year, month)


@router.post("/save")
def save(date: str = Form(...), memo: str = Form(""), author: str = Form("")):
    # basic validation: YYYY-MM-DD
    if len(date) != 10 or date[4] != "-" or date[7] != "-":
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    memo = (memo or "").strip()
    if len(memo) > 5000:
        raise HTTPException(status_code=400, detail="Memo too long")
    upsert_calendar_memo(date=date, memo=memo, author=(author or "").strip())
    return {"ok": True}

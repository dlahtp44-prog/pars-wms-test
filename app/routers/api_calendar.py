from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from app.db import get_db

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

@router.get("/note")
def get_note(date: str) -> Dict[str, Any]:
    """Get memo for a specific date (YYYY-MM-DD)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT memo, updated_at FROM calendar_notes WHERE memo_date = ?", (date,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"date": date, "memo": "", "updated_at": None}
    return {"date": date, "memo": row[0] or "", "updated_at": row[1]}

@router.post("/note")
def set_note(
    date: str = Form(...),
    memo: str = Form("")
) -> Dict[str, Any]:
    """Upsert memo for a date."""
    date = (date or "").strip()
    if not date:
        raise HTTPException(status_code=400, detail="date is required")
    # basic validation
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")

    memo = (memo or "").strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO calendar_notes (memo_date, memo, updated_at)
           VALUES (?, ?, ?)
           ON CONFLICT(memo_date) DO UPDATE SET memo=excluded.memo, updated_at=excluded.updated_at
        """,
        (date, memo, now),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "date": date, "updated_at": now}

@router.get("/month")
def get_month(year: int, month: int) -> Dict[str, Any]:
    """Return all memos in a month."""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="month must be 1-12")
    y = int(year); m = int(month)
    start = f"{y:04d}-{m:02d}-01"
    # next month start
    if m == 12:
        end = f"{y+1:04d}-01-01"
    else:
        end = f"{y:04d}-{m+1:02d}-01"

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """SELECT memo_date, memo, updated_at
           FROM calendar_notes
           WHERE memo_date >= ? AND memo_date < ?
           ORDER BY memo_date ASC
        """,
        (start, end),
    )
    rows = cur.fetchall()
    conn.close()

    items = [{"date": d, "memo": memo or "", "updated_at": ua} for (d, memo, ua) in rows]
    return {"year": y, "month": m, "items": items}

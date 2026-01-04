from fastapi import APIRouter, Form, HTTPException, Query
from app.db import get_db
from datetime import datetime

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@router.get("/get")
def get_memo(date: str = Query(..., description="YYYY-MM-DD")):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT memo_date, content, author, created_at, updated_at FROM calendar_memos WHERE memo_date = ?", (date,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"date": date, "content": "", "author": "", "created_at": None, "updated_at": None}
    return {"date": row[0], "content": row[1], "author": row[2], "created_at": row[3], "updated_at": row[4]}

@router.get("/month")
def month_memos(year: int = Query(...), month: int = Query(...)):
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="month must be 1-12")
    ym = f"{year:04d}-{month:02d}-"
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT memo_date, content, author, updated_at FROM calendar_memos WHERE memo_date LIKE ?",
        (ym + "%",),
    )
    rows = cur.fetchall()
    conn.close()
    return [{"date": r[0], "content": r[1], "author": r[2], "updated_at": r[3]} for r in rows]

@router.post("/save")
def save_memo(
    date: str = Form(...),
    content: str = Form(""),
    author: str = Form(""),
):
    date = (date or "").strip()
    content = (content or "").strip()
    author = (author or "").strip()

    if not date:
        raise HTTPException(status_code=400, detail="date required")
    if len(content) > 2000:
        raise HTTPException(status_code=400, detail="content too long (max 2000)")

    now = _now()
    conn = get_db()
    cur = conn.cursor()
    # Upsert by memo_date (one memo per day)
    cur.execute(
        """
        INSERT INTO calendar_memos (memo_date, content, author, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(memo_date) DO UPDATE SET
            content = excluded.content,
            author = excluded.author,
            updated_at = excluded.updated_at
        """,
        (date, content, author, now, now),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "date": date, "updated_at": now}

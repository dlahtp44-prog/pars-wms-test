from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Request, Form, Query, HTTPException
from app.auth import get_user_session
from app.db import get_db

router = APIRouter(prefix="/api/calendar", tags=["api-calendar"])

@router.get("/memos")
def list_memos(request: Request, memo_date: str = Query(..., description="YYYY-MM-DD")):
    user = get_user_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    d = (memo_date or "").strip()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, memo_date, content, created_by, created_at, updated_at
            FROM calendar_memo
            WHERE memo_date = ?
            ORDER BY id DESC""",
        (d,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "memo_date": r["memo_date"],
            "content": r["content"],
            "created_by": r["created_by"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]

@router.post("/memos")
def add_memo(request: Request, memo_date: str = Form(...), content: str = Form(...)):
    user = get_user_session(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    d = (memo_date or "").strip()
    c = (content or "").strip()
    if not d or not c:
        raise HTTPException(status_code=400, detail="날짜/메모가 필요합니다.")
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO calendar_memo (memo_date, content, created_by, created_at, updated_at)
            VALUES (?,?,?,?,?)""",
        (d, c, user.username, now, now),
    )
    conn.commit()
    conn.close()
    return {"ok": True}

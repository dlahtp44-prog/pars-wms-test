from fastapi import APIRouter, Form, HTTPException, Query
from datetime import datetime
from app.db import get_db

router = APIRouter(prefix="/api/memos", tags=["memos"])

@router.get("")
def list_memos(month: str = Query(..., description="YYYY-MM")):
    if len(month) != 7 or month[4] != "-":
        raise HTTPException(status_code=400, detail="month는 YYYY-MM 형식이어야 합니다.")
    prefix = month + "-"
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT memo_date, content FROM memos WHERE memo_date LIKE ? ORDER BY memo_date ASC", (prefix + "%",))
    rows = [{"memo_date": r[0], "content": r[1]} for r in cur.fetchall()]
    conn.close()
    return {"items": rows}

@router.post("")
def upsert_memo(memo_date: str = Form(...), content: str = Form(...)):
    # memo_date: YYYY-MM-DD
    if len(memo_date) != 10 or memo_date[4] != "-" or memo_date[7] != "-":
        raise HTTPException(status_code=400, detail="memo_date는 YYYY-MM-DD 형식이어야 합니다.")
    now = datetime.now().isoformat(timespec="seconds")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM memos WHERE memo_date=?", (memo_date,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE memos SET content=? WHERE memo_date=?", (content, memo_date))
    else:
        cur.execute("INSERT INTO memos(memo_date, content, created_at) VALUES(?, ?, ?)", (memo_date, content, now))
    conn.commit()
    conn.close()
    return {"ok": True}

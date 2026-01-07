from fastapi import APIRouter
from app.db.database import get_conn

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("")
def history():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

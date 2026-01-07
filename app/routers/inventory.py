from fastapi import APIRouter
from app.db.database import get_conn

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

@router.get("")
def inventory():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory")
    rows = cur.fetchall()
    conn.close()
    return rows

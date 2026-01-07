from fastapi import APIRouter, Form
from app.db.database import get_conn
from datetime import datetime

router = APIRouter(prefix="/api/inbound", tags=["inbound"])

@router.post("")
def inbound(item_code: str = Form(...), qty: int = Form(...), location: str = Form(...)):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO history(type, item_code, qty, location, created_at) VALUES (?,?,?,?,?)",
                ("IN", item_code, qty, location, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return {"result": "inbound ok"}

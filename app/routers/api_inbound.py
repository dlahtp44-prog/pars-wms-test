from fastapi import APIRouter, Form, HTTPException
from datetime import datetime
from app.db import db
router=APIRouter(prefix="/api/inbound", tags=["inbound"])
@router.post("")
def inbound(warehouse:str=Form(...), location:str=Form(...), brand:str=Form(""), item_code:str=Form(...), item_name:str=Form(...),
            lot:str=Form(...), spec:str=Form(...), qty:int=Form(...), note:str=Form(""), operator:str=Form("")):
    if qty<=0: raise HTTPException(400,"수량은 1 이상")
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db() as conn:
        cur=conn.cursor()
        row=cur.execute("SELECT id,qty FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?",
                        (warehouse,location,item_code,lot,spec)).fetchone()
        if row:
            cur.execute("UPDATE inventory SET qty=?, item_name=?, brand=?, note=?, updated_at=? WHERE id=?",
                        (int(row["qty"])+qty, item_name, brand, note, now, row["id"]))
        else:
            cur.execute("INSERT INTO inventory(warehouse,location,brand,item_code,item_name,lot,spec,qty,note,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (warehouse,location,brand,item_code,item_name,lot,spec,qty,note,now))
        cur.execute("INSERT INTO history(created_at,type,warehouse,location,brand,item_code,item_name,lot,spec,qty,note,operator) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (now,"INBOUND",warehouse,location,brand,item_code,item_name,lot,spec,qty,note,operator))
    return {"ok":True}

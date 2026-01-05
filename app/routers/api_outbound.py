from fastapi import APIRouter, Form, HTTPException
from datetime import datetime
from app.db import db
router=APIRouter(prefix="/api/outbound", tags=["outbound"])
@router.post("")
def outbound(warehouse:str=Form(...), location:str=Form(...), item_code:str=Form(...), lot:str=Form(...), spec:str=Form(...),
             qty:int=Form(...), note:str=Form(""), operator:str=Form("")):
    if qty<=0: raise HTTPException(400,"수량은 1 이상")
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db() as conn:
        cur=conn.cursor()
        row=cur.execute("SELECT id,qty,item_name,brand FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?",
                        (warehouse,location,item_code,lot,spec)).fetchone()
        if not row: raise HTTPException(404,"재고 없음")
        if int(row["qty"])<qty: raise HTTPException(400,f"재고 부족: 현재 {row['qty']}")
        cur.execute("UPDATE inventory SET qty=?, updated_at=? WHERE id=?",(int(row["qty"])-qty,now,row["id"]))
        cur.execute("INSERT INTO history(created_at,type,warehouse,location,brand,item_code,item_name,lot,spec,qty,note,operator) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (now,"OUTBOUND",warehouse,location,row["brand"],item_code,row["item_name"],lot,spec,qty,note,operator))
    return {"ok":True}

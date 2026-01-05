from fastapi import APIRouter, Form, HTTPException
from datetime import datetime
from app.db import db
router=APIRouter(prefix="/api/move", tags=["move"])
@router.post("")
def move(warehouse:str=Form(...), item_code:str=Form(...), item_name:str=Form(""), lot:str=Form(...), spec:str=Form(...),
         from_location:str=Form(...), to_location:str=Form(...), qty:int=Form(...), note:str=Form(""), operator:str=Form("")):
    if qty<=0: raise HTTPException(400,"수량은 1 이상")
    if from_location==to_location: raise HTTPException(400,"출발/도착 동일")
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db() as conn:
        cur=conn.cursor()
        src=cur.execute("SELECT id,qty,item_name,brand FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?",
                        (warehouse,from_location,item_code,lot,spec)).fetchone()
        if not src: raise HTTPException(404,"출발 재고 없음")
        if int(src["qty"])<qty: raise HTTPException(400,f"재고 부족: 현재 {src['qty']}")
        cur.execute("UPDATE inventory SET qty=?, updated_at=? WHERE id=?",(int(src["qty"])-qty,now,src["id"]))
        dst=cur.execute("SELECT id,qty FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?",
                        (warehouse,to_location,item_code,lot,spec)).fetchone()
        item_name_final=item_name or src["item_name"] or ""
        brand_final=src["brand"] or ""
        if dst:
            cur.execute("UPDATE inventory SET qty=?, item_name=?, brand=?, updated_at=? WHERE id=?",
                        (int(dst["qty"])+qty,item_name_final,brand_final,now,dst["id"]))
        else:
            cur.execute("INSERT INTO inventory(warehouse,location,brand,item_code,item_name,lot,spec,qty,note,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (warehouse,to_location,brand_final,item_code,item_name_final,lot,spec,qty,note,now))
        cur.execute("INSERT INTO history(created_at,type,warehouse,from_location,to_location,brand,item_code,item_name,lot,spec,qty,note,operator) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (now,"MOVE",warehouse,from_location,to_location,brand_final,item_code,item_name_final,lot,spec,qty,note,operator))
    return {"ok":True}

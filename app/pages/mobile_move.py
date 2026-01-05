from fastapi import APIRouter, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.db import db
from app.utils.qr_format import parse_qr
templates=Jinja2Templates(directory=str(TEMPLATES_DIR))
router=APIRouter(prefix="/m/move", tags=["mobile"])
@router.get("/select", response_class=HTMLResponse)
def select_item(request:Request, warehouse:str=Query("MAIN"), from_location:str=Query(...)):
    with db() as conn:
        rows=conn.execute("SELECT * FROM inventory WHERE warehouse=? AND location=? AND qty>0 ORDER BY item_name",(warehouse,from_location)).fetchall()
    return templates.TemplateResponse("m/move_select.html",{"request":request,"warehouse":warehouse,"from_location":from_location,"rows":rows})
@router.get("/to", response_class=HTMLResponse)
def to_page(request:Request, warehouse:str=Query("MAIN"), from_location:str=Query(...), item_code:str=Query(...), lot:str=Query(...), spec:str=Query(...)):
    with db() as conn:
        r=conn.execute("SELECT item_name,qty FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot=? AND spec=?",(warehouse,from_location,item_code,lot,spec)).fetchone()
    return templates.TemplateResponse("m/move_to.html",{"request":request,"warehouse":warehouse,"from_location":from_location,"item_code":item_code,"item_name":(r["item_name"] if r else ""),"lot":lot,"spec":spec,"available_qty":(int(r["qty"]) if r else 0),"error":""})
@router.post("/to/submit")
def to_submit(warehouse:str=Form("MAIN"), from_location:str=Form(...), item_code:str=Form(...), item_name:str=Form(""), lot:str=Form(...), spec:str=Form(...), available_qty:int=Form(0),
              to_qr:str=Form(...), qty:int=Form(...), note:str=Form("")):
    data=parse_qr(to_qr)
    to_location=data.get("location","") or to_qr.strip()
    if not to_location or qty<=0: 
        return RedirectResponse(f"/m/move/to?warehouse={warehouse}&from_location={from_location}&item_code={item_code}&lot={lot}&spec={spec}",302)
    if available_qty and qty>int(available_qty):
        return RedirectResponse(f"/m/move/to?warehouse={warehouse}&from_location={from_location}&item_code={item_code}&lot={lot}&spec={spec}",302)
    from app.routers.api_move import move as api_move
    api_move(warehouse=warehouse,item_code=item_code,item_name=item_name,lot=lot,spec=spec,from_location=from_location,to_location=to_location,qty=qty,note=note,operator="mobile")
    return RedirectResponse(f"/m/move/done?warehouse={warehouse}&from_location={from_location}&to_location={to_location}&item_code={item_code}&item_name={item_name}&lot={lot}&spec={spec}&qty={qty}",302)
@router.get("/done", response_class=HTMLResponse)
def done(request:Request, warehouse:str, from_location:str, to_location:str, item_code:str, item_name:str, lot:str, spec:str, qty:int):
    return templates.TemplateResponse("m/move_done.html",{"request":request,"warehouse":warehouse,"from_location":from_location,"to_location":to_location,"item_code":item_code,"item_name":item_name,"lot":lot,"spec":spec,"qty":qty})

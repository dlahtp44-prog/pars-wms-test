from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db import db
templates=Jinja2Templates(directory=str(TEMPLATES_DIR))
router=APIRouter(prefix="/m/qr", tags=["mobile"])
@router.get("/inventory", response_class=HTMLResponse)
def inventory_detail(request:Request, warehouse:str=Query("MAIN"), location:str=Query(...)):
    with db() as conn:
        rows=conn.execute("SELECT * FROM inventory WHERE warehouse=? AND location=? ORDER BY item_name",(warehouse,location)).fetchall()
    return templates.TemplateResponse("m/inventory_detail.html",{"request":request,"warehouse":warehouse,"location":location,"rows":rows})

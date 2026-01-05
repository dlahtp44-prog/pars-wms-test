from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db import db
templates=Jinja2Templates(directory=str(TEMPLATES_DIR))
router=APIRouter(prefix="/page/inventory", tags=["page"])
@router.get("", response_class=HTMLResponse)
def page(request:Request, limit:int=Query(200,ge=1,le=5000)):
    with db() as conn:
        rows=conn.execute("SELECT * FROM inventory ORDER BY updated_at DESC LIMIT ?",(limit,)).fetchall()
    return templates.TemplateResponse("inventory.html",{"request":request,"rows":rows,"limit":limit})

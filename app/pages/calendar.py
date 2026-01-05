from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db import db
templates=Jinja2Templates(directory=str(TEMPLATES_DIR))
router=APIRouter(prefix="/page/calendar", tags=["page"])
@router.get("", response_class=HTMLResponse)
def page(request:Request, date:str=Query("")):
    memo=""
    if date:
        with db() as conn:
            r=conn.execute("SELECT memo FROM calendar_memo WHERE memo_date=?",(date,)).fetchone()
            if r: memo=r["memo"]
    return templates.TemplateResponse("calendar.html",{"request":request,"date":date,"memo":memo})

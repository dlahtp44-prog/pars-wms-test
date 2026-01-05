from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
templates=Jinja2Templates(directory=str(TEMPLATES_DIR))
router=APIRouter(prefix="/page/inbound", tags=["page"])
@router.get("", response_class=HTMLResponse)
def page(request:Request):
    return templates.TemplateResponse("inbound.html",{"request":request})

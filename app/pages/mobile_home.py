from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
templates=Jinja2Templates(directory=str(TEMPLATES_DIR))
router=APIRouter(prefix="/m", tags=["mobile"])
@router.get("", response_class=HTMLResponse)
def home(request:Request):
    return templates.TemplateResponse("m/home.html",{"request":request})

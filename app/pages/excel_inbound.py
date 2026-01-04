from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/page", tags=["Excel Inbound"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/excel/inbound", response_class=HTMLResponse)
def excel_inbound(request: Request):
    return templates.TemplateResponse("excel_inbound.html", {"request": request})

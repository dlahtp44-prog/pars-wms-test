from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/page", tags=["pages"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/excel", response_class=HTMLResponse)
def center(request: Request):
    return templates.TemplateResponse("excel_center.html", {"request": request})

@router.get("/excel/inbound", response_class=HTMLResponse)
def excel_inbound_page(request: Request):
    return templates.TemplateResponse("excel/inbound.html", {"request": request})

@router.get("/excel/outbound", response_class=HTMLResponse)
def excel_outbound_page(request: Request):
    return templates.TemplateResponse("excel/outbound.html", {"request": request})

@router.get("/excel/move", response_class=HTMLResponse)
def excel_move_page(request: Request):
    return templates.TemplateResponse("excel/move.html", {"request": request})

@router.get("/excel/inventory", response_class=HTMLResponse)
def excel_inventory_page(request: Request):
    return templates.TemplateResponse("excel/inventory.html", {"request": request})

@router.get("/excel/history", response_class=HTMLResponse)
def excel_history_page(request: Request):
    return templates.TemplateResponse("excel/history.html", {"request": request})

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR

router = APIRouter(tags=["page-label-print"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/label/item", response_class=HTMLResponse)
def label_item(request: Request):
    return templates.TemplateResponse("label_item.html", {"request": request})

@router.get("/label/location", response_class=HTMLResponse)
def label_location(request: Request):
    return templates.TemplateResponse("label_location.html", {"request": request})

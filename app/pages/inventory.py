from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory

router = APIRouter(prefix="/page/inventory", tags=["page-inventory"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("", response_class=HTMLResponse)
def page(request: Request, location: str="", item_code: str=""):
    rows = query_inventory(location=location, item_code=item_code)
    return templates.TemplateResponse("inventory.html", {"request": request, "rows": rows, "location": location, "item_code": item_code})

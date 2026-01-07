from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/damage", tags=["page-damage"])

@router.get("", response_class=HTMLResponse)
def damage_page(
    request: Request,
    warehouse: str = "",
    location: str = "",
    brand: str = "",
    item_code: str = "",
    item_name: str = "",
    lot: str = "",
    spec: str = "",
):
    return templates.TemplateResponse(
        "damage.html",
        {
            "request": request,
            "warehouse": warehouse,
            "location": location,
            "brand": brand,
            "item_code": item_code,
            "item_name": item_name,
            "lot": lot,
            "spec": spec,
        }
    )

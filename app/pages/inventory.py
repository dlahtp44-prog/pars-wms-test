from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/page", tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/inventory")
def page_inventory(
    request: Request,
    warehouse: str = "",
    location: str = "",
    item_code: str = "",
    lot: str = "",
    spec: str = "",
):
    filters = {
        "warehouse": warehouse,
        "location": location,
        "item_code": item_code,
        "lot": lot,
        "spec": spec,
    }
    return templates.TemplateResponse(
        "inventory.html",
        {"request": request, "filters": filters},
    )

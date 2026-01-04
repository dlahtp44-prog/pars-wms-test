from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/m", tags=["Mobile Inventory"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/inventory")
def mobile_inventory(request: Request, qr: str):
    return templates.TemplateResponse(
        "mobile/inventory_detail.html",
        {
            "request": request,
            "location": qr.strip()
        }
    )

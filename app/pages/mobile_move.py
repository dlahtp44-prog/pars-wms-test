from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/m", tags=["Mobile Move"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/move")
def move_start(request: Request, qr: str):
    return templates.TemplateResponse(
        "mobile/move_select.html",
        {"request": request, "location": qr.strip()}
    )

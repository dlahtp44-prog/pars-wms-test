from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/page", tags=["calendar-page"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/calendar")
def calendar_page(request: Request):
    return templates.TemplateResponse("calendar.html", {"request": request})

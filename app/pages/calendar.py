from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/page", tags=["Calendar"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/calendar", response_class=HTMLResponse)
def calendar_page(request: Request):
    return templates.TemplateResponse("calendar.html", {"request": request})

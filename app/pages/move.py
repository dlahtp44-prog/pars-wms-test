from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/page", tags=["pages"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/move", response_class=HTMLResponse)
def page(request: Request):
    return templates.TemplateResponse("move.html", {"request": request})

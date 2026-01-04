from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from datetime import datetime

router = APIRouter(prefix="/page", tags=["Calendar"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/calendar")
def calendar_page(request: Request):
    # default to current month
    now = datetime.now()
    return templates.TemplateResponse(
        "calendar.html",
        {"request": request, "year": now.year, "month": now.month}
    )

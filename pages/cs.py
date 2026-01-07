from datetime import date
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.core.auth import require_admin
from app.db import list_cs_tickets

router = APIRouter(prefix="/page/cs", tags=["page-cs"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("", response_class=HTMLResponse)
def cs_home(request: Request, y: int = 0, m: int = 0):
    user = require_admin(request)
    today = date.today()
    y = y or today.year
    m = m or today.month
    rows = list_cs_tickets(y, m)
    return templates.TemplateResponse(
        "cs.html",
        {"request": request, "user": user, "year": y, "month": m, "rows": rows},
    )

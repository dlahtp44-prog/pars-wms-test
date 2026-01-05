from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import date as dt_date
from ..core.paths import TEMPLATES_DIR
from ..db import get_db

router = APIRouter(prefix="/page", tags=["pages"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/calendar", response_class=HTMLResponse)
def page(request: Request, date: str | None = Query(None)):
    if not date:
        date = dt_date.today().isoformat()
    with get_db() as conn:
        row = conn.execute("SELECT memo, updated_at FROM calendar_memo WHERE date=?", (date,)).fetchone()
    return templates.TemplateResponse("calendar.html", {"request": request, "date": date, "memo": (row["memo"] if row else ""), "updated_at": (row["updated_at"] if row else "")})

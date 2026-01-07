from datetime import date, datetime
import calendar as pycal
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import get_db

router = APIRouter(prefix="/page/calendar", tags=["calendar-page"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _month_range(month: str) -> tuple[int,int]:
    # month: YYYY-MM
    y, m = month.split("-")
    return int(y), int(m)


@router.get("", response_class=HTMLResponse)
def calendar_view(request: Request, month: str = Query(default="")):
    today = date.today()
    if not month:
        month = f"{today.year:04d}-{today.month:02d}"

    y, m = _month_range(month)
    cal = pycal.Calendar(firstweekday=0)  # Monday
    weeks = cal.monthdatescalendar(y, m)

    # fetch memos in this month
    prefix = f"{y:04d}-{m:02d}-"
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT memo_date, content FROM memos WHERE memo_date LIKE ?", (prefix + "%",))
    memos = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()

    return templates.TemplateResponse(
        "calendar.html",
        {
            "request": request,
            "month": month,
            "weeks": weeks,
            "memos": memos,
            "today": today.isoformat(),
        },
    )

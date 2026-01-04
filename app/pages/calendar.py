from __future__ import annotations

import calendar as cal
from datetime import date, datetime
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.auth import get_user_session
from app.db import get_db

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(prefix="/page", tags=["calendar"])

def _require_login_page(request: Request):
    user = get_user_session(request)
    if not user:
        return None
    return user

@router.get("/calendar", response_class=HTMLResponse)
def calendar_page(request: Request, year: int | None = None, month: int | None = None):
    user = _require_login_page(request)
    if not user:
        return RedirectResponse(url="/login?next=/page/calendar", status_code=303)

    today = datetime.now().date()
    y = int(year or today.year)
    m = int(month or today.month)
    m = 1 if m < 1 else (12 if m > 12 else m)

    first_weekday, days_in_month = cal.monthrange(y, m)  # weekday: Mon=0
    # build weeks grid (Sun first for KR)
    # convert to Sun=0 format
    first_weekday_sun0 = (first_weekday + 1) % 7

    grid = []
    week = [0]*7
    day = 1
    # fill first week
    for i in range(first_weekday_sun0, 7):
        week[i] = day
        day += 1
    grid.append(week)
    while day <= days_in_month:
        week = [0]*7
        for i in range(7):
            if day <= days_in_month:
                week[i] = day
                day += 1
        grid.append(week)

    # memo counts for month
    conn = get_db()
    cur = conn.cursor()
    start = date(y, m, 1).isoformat()
    end = date(y, m, days_in_month).isoformat()
    cur.execute(
        """SELECT memo_date, COUNT(*) AS cnt
            FROM calendar_memo
            WHERE memo_date BETWEEN ? AND ?
            GROUP BY memo_date""",
        (start, end),
    )
    counts = {row["memo_date"]: int(row["cnt"]) for row in cur.fetchall()}
    conn.close()

    # prev / next
    if m == 1:
        prev_y, prev_m = y-1, 12
    else:
        prev_y, prev_m = y, m-1
    if m == 12:
        next_y, next_m = y+1, 1
    else:
        next_y, next_m = y, m+1

    return templates.TemplateResponse(
        "calendar.html",
        {
            "request": request,
            "user": user,
            "year": y,
            "month": m,
            "grid": grid,
            "counts": counts,
            "today": today.isoformat(),
            "prev_y": prev_y,
            "prev_m": prev_m,
            "next_y": next_y,
            "next_m": next_m,
        },
    )

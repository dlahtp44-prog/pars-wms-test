from datetime import date, datetime
import calendar as _cal

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db

router = APIRouter(prefix="/page", tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


def _parse_month(month_str: str) -> date:
    """'YYYY-MM' -> date(YYYY, MM, 1)"""
    try:
        y, m = (month_str or "").split("-", 1)
        return date(int(y), int(m), 1)
    except Exception:
        today = date.today()
        return date(today.year, today.month, 1)


def _add_month(d: date, delta: int) -> date:
    y = d.year + (d.month - 1 + delta) // 12
    m = (d.month - 1 + delta) % 12 + 1
    return date(y, m, 1)


@router.get("/calendar", response_class=HTMLResponse)
def calendar_page(request: Request, month: str = "", pick: str = ""):
    """월 달력 + 일자 메모 편집"""

    month_start = _parse_month(month)
    month_label = month_start.strftime("%Y-%m")
    prev_month = _add_month(month_start, -1).strftime("%Y-%m")
    next_month = _add_month(month_start, 1).strftime("%Y-%m")

    # 월 범위
    last_day = _cal.monthrange(month_start.year, month_start.month)[1]
    start_str = month_start.strftime("%Y-%m-01")
    end_str = date(month_start.year, month_start.month, last_day).strftime("%Y-%m-%d")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT date, memo, updated_at
        FROM calendar_memo
        WHERE date BETWEEN ? AND ?
        """,
        (start_str, end_str),
    )
    memo_rows = cur.fetchall()
    memo_map = {r["date"]: (r["memo"] or "") for r in memo_rows}

    # 달력 그리드(월요일 시작)
    cal = _cal.Calendar(firstweekday=0)  # 0=Monday
    weeks = []
    for week in cal.monthdatescalendar(month_start.year, month_start.month):
        row = []
        for d in week:
            if d.month != month_start.month:
                row.append({"date": d.isoformat(), "day": d.day, "in_month": False, "memo": ""})
            else:
                ds = d.isoformat()
                row.append({"date": ds, "day": d.day, "in_month": True, "memo": memo_map.get(ds, "")})
        weeks.append(row)

    # 선택일(편집)
    if pick:
        try:
            pick_date = datetime.strptime(pick, "%Y-%m-%d").date()
        except Exception:
            pick_date = date.today()
    else:
        pick_date = date.today()
        if pick_date.month != month_start.month or pick_date.year != month_start.year:
            pick_date = month_start

    pick_str = pick_date.isoformat()
    cur.execute("SELECT memo, updated_at FROM calendar_memo WHERE date=?", (pick_str,))
    one = cur.fetchone()
    memo = (one["memo"] if one else "") or ""
    updated_at = (one["updated_at"] if one else "") or ""

    return templates.TemplateResponse(
        "calendar.html",
        {
            "request": request,
            "month": month_label,
            "prev_month": prev_month,
            "next_month": next_month,
            "weeks": weeks,
            "pick": pick_str,
            "memo": memo,
            "updated_at": updated_at,
        },
    )

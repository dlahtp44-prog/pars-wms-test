from io import BytesIO
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from openpyxl import Workbook

from app.core.paths import TEMPLATES_DIR
from app.db import query_history

router = APIRouter(prefix="/page/history", tags=["page-history"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def _to_int(v, default=None):
    try:
        if v is None or v == "":
            return default
        return int(v)
    except Exception:
        return default

@router.get("", response_class=HTMLResponse)
def history_page(
    request: Request,
    year: str = "",
    month: str = "",
    day: str = "",
    limit: str = "300",
):
    y = _to_int(year, None)
    m = _to_int(month, None)
    d = _to_int(day, None)
    lim = _to_int(limit, 300) or 300

    rows = query_history(y, m, d, lim)

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "rows": rows,
            "year": year,
            "month": month,
            "day": day,
            "limit": limit,
        },
    )

@router.get("/excel")
def history_excel(
    year: str = "",
    month: str = "",
    day: str = "",
    limit: str = "2000",
):
    y = _to_int(year, None)
    m = _to_int(month, None)
    d = _to_int(day, None)
    lim = _to_int(limit, 2000) or 2000

    rows = query_history(y, m, d, lim)

    wb = Workbook()
    ws = wb.active
    ws.title = "history"

    headers = [
        "created_at", "type", "warehouse",
        "item_code", "item_name", "lot", "spec",
        "from_location", "to_location", "qty", "note"
    ]
    ws.append(headers)

    for r in rows:
        ws.append([
            r.get("created_at"),
            r.get("type"),
            r.get("warehouse"),
            r.get("item_code"),
            r.get("item_name"),
            r.get("lot"),
            r.get("spec"),
            r.get("from_location"),
            r.get("to_location"),
            r.get("qty"),
            r.get("note"),
        ])

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"history_{stamp}.xlsx"

    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

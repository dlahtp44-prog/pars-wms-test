from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import csv
import io

from app.db import get_db

router = APIRouter(prefix="/page/history", tags=["history"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def history_page(request: Request):
    return templates.TemplateResponse(
        "history.html",
        {"request": request}
    )


@router.get("/excel")
def history_excel(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    day: Optional[int] = Query(None),
):
    conn = get_db()
    cur = conn.cursor()

    sql = "SELECT * FROM history WHERE 1=1"
    params = []

    if year:
        sql += " AND strftime('%Y', created_at) = ?"
        params.append(f"{year:04d}")
    if month:
        sql += " AND strftime('%m', created_at) = ?"
        params.append(f"{month:02d}")
    if day:
        sql += " AND strftime('%d', created_at) = ?"
        params.append(f"{day:02d}")

    sql += " ORDER BY created_at DESC"

    cur.execute(sql, params)
    rows = cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([d[0] for d in cur.description])
    writer.writerows(rows)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=history.csv"
        },
    )

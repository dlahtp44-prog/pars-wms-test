from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook
from io import BytesIO
from ..core.paths import TEMPLATES_DIR
from ..db import get_db

router = APIRouter(prefix="/page", tags=["pages"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/history", response_class=HTMLResponse)
def page(request: Request,
         year: int | None = None,
         month: int | None = None,
         day: int | None = None,
         limit: int = Query(300, ge=1, le=2000)):
    with get_db() as conn:
        cur = conn.cursor()
        q="SELECT * FROM history WHERE 1=1"
        params=[]
        if year:
            q += " AND substr(created_at,1,4)=?"
            params.append(f"{year:04d}")
        if month:
            q += " AND substr(created_at,6,2)=?"
            params.append(f"{month:02d}")
        if day:
            q += " AND substr(created_at,9,2)=?"
            params.append(f"{day:02d}")
        q += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(limit)
        rows=cur.execute(q, params).fetchall()
    return templates.TemplateResponse("history.html", {"request": request, "rows": rows, "year": year or "", "month": month or "", "day": day or "", "limit": limit})

@router.get("/history/excel")
def history_excel(year: int | None = None, month: int | None = None, day: int | None = None):
    with get_db() as conn:
        cur = conn.cursor()
        q="SELECT * FROM history WHERE 1=1"
        params=[]
        if year:
            q += " AND substr(created_at,1,4)=?"
            params.append(f"{year:04d}")
        if month:
            q += " AND substr(created_at,6,2)=?"
            params.append(f"{month:02d}")
        if day:
            q += " AND substr(created_at,9,2)=?"
            params.append(f"{day:02d}")
        q += " ORDER BY created_at DESC, id DESC"
        rows=cur.execute(q, params).fetchall()

    wb=Workbook()
    ws=wb.active
    ws.title="history"
    headers=["시간","유형","창고","로케이션","출발","도착","브랜드","품번","품명","LOT","규격","수량","비고","작업자"]
    ws.append(headers)
    for r in rows:
        ws.append([
            r["created_at"], r["type"], r["warehouse"], r["location"], r["from_location"], r["to_location"],
            r["brand"], r["item_code"], r["item_name"], r["lot"], r["spec"], r["qty"], r["note"], r["operator"]
        ])
    bio=BytesIO()
    wb.save(bio)
    bio.seek(0)
    filename="history.xlsx"
    return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})

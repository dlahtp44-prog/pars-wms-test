from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from io import BytesIO
from openpyxl import Workbook

from app.core.paths import TEMPLATES_DIR
from app.db import query_history

router = APIRouter(prefix="/page/history", tags=["page-history"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("", response_class=HTMLResponse)
def page(request: Request, limit: int=200):
    rows = query_history(limit=limit)
    return templates.TemplateResponse("history.html", {"request": request, "rows": rows, "limit": limit})

@router.get("/excel")
def excel(year: int | None = None, month: int | None = None, day: int | None = None, limit: int = 100000):
    # query_history already returns latest; we filter in python if date params provided
    rows = query_history(limit=limit)

    if year or month or day:
        def match(r):
            # history table: (id, created_at, type, warehouse, item_code, item_name, lot, spec, from_location, to_location, qty, note)
            created_at = str(r[1])  # 'YYYY-MM-DD ...'
            y = int(created_at[0:4]) if len(created_at)>=4 else None
            m = int(created_at[5:7]) if len(created_at)>=7 else None
            d = int(created_at[8:10]) if len(created_at)>=10 else None
            if year and y != year: return False
            if month and m != month: return False
            if day and d != day: return False
            return True
        rows = [r for r in rows if match(r)]

    wb = Workbook()
    ws = wb.active
    ws.title = "history"
    ws.append(["id","created_at","type","창고","품번","품명","LOT","규격","FROM","TO","수량","비고"])
    for r in rows:
        ws.append(list(r))

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    filename = "history.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

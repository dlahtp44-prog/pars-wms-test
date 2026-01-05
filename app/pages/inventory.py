from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook
from io import BytesIO

from ..core.paths import TEMPLATES_DIR
from ..db import get_db

router = APIRouter(prefix="/page", tags=["pages"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def _fetch(warehouse: str | None, location: str | None, limit: int | None):
    with get_db() as conn:
        cur = conn.cursor()
        q="SELECT * FROM inventory WHERE 1=1"
        params=[]
        if warehouse:
            q+=" AND warehouse=?"
            params.append(warehouse)
        if location:
            q+=" AND location=?"
            params.append(location)
        q+=" ORDER BY updated_at DESC"
        if limit:
            q+=" LIMIT ?"
            params.append(limit)
        rows=cur.execute(q, params).fetchall()
    return rows

@router.get("/inventory", response_class=HTMLResponse)
def page(request: Request, limit: int = Query(200, ge=1, le=2000), warehouse: str | None = None, location: str | None = None):
    rows=_fetch(warehouse, location, limit)
    return templates.TemplateResponse("inventory.html", {"request": request, "rows": rows, "limit": limit, "warehouse": warehouse or "", "location": location or ""})

@router.get("/inventory/excel")
def inventory_excel(warehouse: str | None = None, location: str | None = None):
    rows=_fetch(warehouse, location, None)
    wb=Workbook()
    ws=wb.active
    ws.title="inventory"
    headers=["업데이트","창고","로케이션","브랜드","품번","품명","LOT","규격","수량","비고"]
    ws.append(headers)
    for r in rows:
        ws.append([r["updated_at"], r["warehouse"], r["location"], r["brand"], r["item_code"], r["item_name"], r["lot"], r["spec"], r["qty"], r["note"]])
    bio=BytesIO()
    wb.save(bio)
    bio.seek(0)
    filename="inventory.xlsx"
    return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})

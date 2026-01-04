from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from io import BytesIO
from openpyxl import Workbook

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory

router = APIRouter(prefix="/page/inventory", tags=["page-inventory"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    warehouse: str = "",
    location: str = "",
    item_code: str = "",
    lot: str = "",
    spec: str = "",
    limit: int = 500,
):
    rows = query_inventory(
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        lot=lot,
        spec=spec,
        limit=limit,
    )
    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "rows": rows,
            "filters": {
                "warehouse": warehouse,
                "location": location,
                "item_code": item_code,
                "lot": lot,
                "spec": spec,
                "limit": limit,
            },
        },
    )

@router.get("/excel")
def excel(
    warehouse: str = "",
    location: str = "",
    item_code: str = "",
    lot: str = "",
    spec: str = "",
    limit: int = 5000,
):
    rows = query_inventory(
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        lot=lot,
        spec=spec,
        limit=limit,
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "inventory"
    ws.append(["창고", "로케이션", "품번", "품명", "LOT", "규격", "수량", "비고", "updated_at"])
    for r in rows:
        # query_inventory returns tuples matching inventory table
        ws.append(list(r))

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    filename = "inventory.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

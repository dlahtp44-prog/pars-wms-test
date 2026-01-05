from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from io import BytesIO
from openpyxl import Workbook
from app.db import db
templates=Jinja2Templates(directory=str(TEMPLATES_DIR))
router=APIRouter(prefix="/page/excel", tags=["page"])
@router.get("", response_class=HTMLResponse)
def home(request:Request):
    return templates.TemplateResponse("excel/index.html",{"request":request})
@router.get("/inbound", response_class=HTMLResponse)
def inbound_page(request:Request):
    return templates.TemplateResponse("excel/inbound.html",{"request":request})
@router.get("/outbound", response_class=HTMLResponse)
def outbound_page(request:Request):
    return templates.TemplateResponse("excel/outbound.html",{"request":request})
@router.get("/move", response_class=HTMLResponse)
def move_page(request:Request):
    return templates.TemplateResponse("excel/move.html",{"request":request})
@router.get("/inventory/download")
def inventory_download():
    with db() as conn:
        rows=conn.execute("SELECT * FROM inventory ORDER BY updated_at DESC").fetchall()
    wb=Workbook(); ws=wb.active; ws.title="inventory"
    ws.append(["창고","로케이션","브랜드","품번","품명","LOT","규격","수량","비고","업데이트"])
    for r in rows:
        ws.append([r["warehouse"],r["location"],r["brand"],r["item_code"],r["item_name"],r["lot"],r["spec"],r["qty"],r["note"],r["updated_at"]])
    bio=BytesIO(); wb.save(bio); bio.seek(0)
    return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition":'attachment; filename="inventory.xlsx"'})

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from io import BytesIO
from openpyxl import Workbook
from app.db import db
templates=Jinja2Templates(directory=str(TEMPLATES_DIR))
router=APIRouter(prefix="/page/history", tags=["page"])
def _date_range(year,month,day):
    if not year: return None
    y=int(year); m=int(month) if month else 1; d=int(day) if day else 1
    if day:
        s=datetime(y,m,d,0,0,0); e=datetime(y,m,d,23,59,59)
    elif month:
        import calendar
        last=calendar.monthrange(y,m)[1]
        s=datetime(y,m,1,0,0,0); e=datetime(y,m,last,23,59,59)
    else:
        s=datetime(y,1,1,0,0,0); e=datetime(y,12,31,23,59,59)
    return s.strftime("%Y-%m-%d %H:%M:%S"), e.strftime("%Y-%m-%d %H:%M:%S")
@router.get("", response_class=HTMLResponse)
def page(request:Request, year:str|None=None, month:str|None=None, day:str|None=None, limit:int=Query(300,ge=1,le=5000)):
    q="SELECT * FROM history"; params=[]
    dr=_date_range(year,month,day)
    if dr:
        q+=" WHERE created_at BETWEEN ? AND ?"; params+=list(dr)
    q+=" ORDER BY created_at DESC LIMIT ?"; params.append(limit)
    with db() as conn:
        rows=conn.execute(q,params).fetchall()
    return templates.TemplateResponse("history.html",{"request":request,"rows":rows,"year":year or "","month":month or "","day":day or "","limit":limit})
@router.get("/excel")
def excel(year:str|None=None, month:str|None=None, day:str|None=None):
    q="SELECT * FROM history"; params=[]
    dr=_date_range(year,month,day)
    if dr:
        q+=" WHERE created_at BETWEEN ? AND ?"; params+=list(dr)
    q+=" ORDER BY created_at DESC"
    with db() as conn:
        rows=conn.execute(q,params).fetchall()
    wb=Workbook(); ws=wb.active; ws.title="history"
    ws.append(["시간","유형","창고","로케이션","출발","도착","브랜드","품번","품명","LOT","규격","수량","비고","작업자"])
    for r in rows:
        ws.append([r["created_at"],r["type"],r["warehouse"],r["location"],r["from_location"],r["to_location"],r["brand"],r["item_code"],r["item_name"],r["lot"],r["spec"],r["qty"],r["note"],r["operator"]])
    bio=BytesIO(); wb.save(bio); bio.seek(0)
    return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition":'attachment; filename="history.xlsx"'})

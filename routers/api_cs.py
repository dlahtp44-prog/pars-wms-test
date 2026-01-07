from datetime import date
from io import BytesIO

from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.auth import require_admin
from app.db import create_cs_ticket, list_cs_tickets, update_cs_ticket, delete_cs_ticket

router = APIRouter(prefix="/api/cs", tags=["api-cs"])

@router.get("/list")
def cs_list(request: Request, year: int, month: int):
    require_admin(request)
    return {"ok": True, "rows": list_cs_tickets(year, month)}

@router.post("/create")
def cs_create(
    request: Request,
    created_date: str = Form(""),
    customer: str = Form(""),
    channel: str = Form(""),
    order_no: str = Form(""),
    item_code: str = Form(""),
    item_name: str = Form(""),
    issue_type: str = Form(""),
    status: str = Form("open"),
    note: str = Form(""),
):
    require_admin(request)
    tid = create_cs_ticket({
        "created_date": created_date or date.today().isoformat(),
        "customer": customer,
        "channel": channel,
        "order_no": order_no,
        "item_code": item_code,
        "item_name": item_name,
        "issue_type": issue_type,
        "status": status,
        "note": note,
    })
    return {"ok": True, "id": tid}

@router.post("/update")
def cs_update(
    request: Request,
    id: int = Form(...),
    created_date: str = Form(""),
    customer: str = Form(""),
    channel: str = Form(""),
    order_no: str = Form(""),
    item_code: str = Form(""),
    item_name: str = Form(""),
    issue_type: str = Form(""),
    status: str = Form(""),
    note: str = Form(""),
):
    require_admin(request)
    fields = {
        "created_date": created_date,
        "customer": customer,
        "channel": channel,
        "order_no": order_no,
        "item_code": item_code,
        "item_name": item_name,
        "issue_type": issue_type,
        "status": status,
        "note": note,
    }
    # empty strings -> ignore
    fields = {k:v for k,v in fields.items() if v != ""}
    update_cs_ticket(int(id), fields)
    return {"ok": True}

@router.post("/delete")
def cs_delete(request: Request, id: int = Form(...)):
    require_admin(request)
    delete_cs_ticket(int(id))
    return {"ok": True}

@router.get("/export.xlsx")
def cs_export_xlsx(request: Request, year: int, month: int):
    require_admin(request)
    rows = list_cs_tickets(year, month)

    try:
        from openpyxl import Workbook
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"openpyxl 로드 실패: {e}")

    wb = Workbook()
    ws = wb.active
    ws.title = f"{year:04d}-{month:02d}"
    headers = ["id","created_date","customer","channel","order_no","item_code","item_name","issue_type","status","note","created_at"]
    ws.append(headers)
    for r in rows:
        ws.append([r.get(h,"") for h in headers])

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    filename = f"cs_{year:04d}_{month:02d}.xlsx"
    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

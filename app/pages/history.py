from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_history
from app.utils.excel_export import rows_to_xlsx_bytes

router = APIRouter(prefix="/page/history", tags=["page-history"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    limit: int = 300,
):
    rows = query_history(limit=limit, year=year, month=month, day=day)
    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "rows": rows,
            "year": year or "",
            "month": month or "",
            "day": day or "",
            "limit": limit,
        },
    )


@router.get("/excel")
def download_excel(
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    limit: int = 2000,
):
    rows = query_history(limit=limit, year=year, month=month, day=day)
    columns = [
        ("created_at", "시간"),
        ("type", "유형"),
        ("warehouse", "창고"),
        ("location", "로케이션"),
        ("from_location", "출발로케이션"),
        ("to_location", "도착로케이션"),
        ("brand", "브랜드"),
        ("item_code", "품번"),
        ("item_name", "품명"),
        ("lot", "LOT"),
        ("spec", "규격"),
        ("qty", "수량"),
        ("note", "비고"),
        ("operator", "작업자"),
    ]
    data = rows_to_xlsx_bytes(rows, columns, sheet_name="이력")
    filename = "history.xlsx"
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

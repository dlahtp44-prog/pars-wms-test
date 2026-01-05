from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db

router = APIRouter(prefix="/page", tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/inventory", response_class=HTMLResponse)
def inventory_page(
    request: Request,
    warehouse: str = "",
    location: str = "",
    limit: int = 200,
    show_zero: int = 0,
):
    """재고조회(현재고)

    - inventory 테이블(현재고 스냅샷)만 조회
    - 기본: 수량 0 제외(show_zero=1이면 포함)
    """

    where = []
    params = {}

    if warehouse:
        where.append("warehouse LIKE :warehouse")
        params["warehouse"] = f"%{warehouse}%"
    if location:
        where.append("location LIKE :location")
        params["location"] = f"%{location}%"
    if not show_zero:
        where.append("qty != 0")

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
        SELECT
            updated_at,
            warehouse,
            location,
            brand,
            item_code,
            item_name,
            lot,
            spec,
            qty
        FROM inventory
        {where_sql}
        ORDER BY location ASC, item_code ASC, lot ASC
        LIMIT :limit
    """

    conn = get_db()
    cur = conn.cursor()
    params["limit"] = max(1, min(int(limit or 200), 2000))
    cur.execute(sql, params)
    rows = cur.fetchall()

    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "rows": rows,
            "warehouse": warehouse,
            "location": location,
            "limit": params["limit"],
            "show_zero": show_zero,
        },
    )

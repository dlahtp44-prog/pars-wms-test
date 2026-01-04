from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.paths import TEMPLATES_DIR
from app.db import get_db

router = APIRouter(prefix="/m/move", tags=["mobile-move"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def move_page(request: Request, location: str = ""):
    """
    출발 로케이션 기준 재고 목록 표시
    """
    items = []
    if location:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT warehouse, location, item_code, item_name, lot, spec, qty
            FROM inventory
            WHERE location = ?
            ORDER BY item_code
        """, (location,))
        items = cur.fetchall()
        conn.close()

    return templates.TemplateResponse(
        "m/move.html",
        {
            "request": request,
            "location": location,
            "items": items,
        },
    )

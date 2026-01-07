from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.utils.qr_format import extract_location_only

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/m/qr/inventory", response_class=HTMLResponse)
def qr_inventory(request: Request):
    raw_location = request.query_params.get("location", "")
    location = extract_location_only(raw_location)

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT warehouse, location, brand, item_code, item_name, lot, spec, qty
        FROM inventory
        WHERE location = ?
        ORDER BY item_code
        """,
        (location,),
    )

    rows = cur.fetchall()

    return templates.TemplateResponse(
        "mobile/qr_inventory.html",
        {
            "request": request,
            "location": location,
            "items": rows,
        },
    )

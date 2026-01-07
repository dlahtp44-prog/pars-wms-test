from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import query_inventory
from app.utils.qr_format import build_item_qr

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(tags=["Mobile Inventory Detail"])

@router.get("/m/inventory/detail", response_class=HTMLResponse)
def inventory_detail(
    request: Request,
    item_code: str = Query(""),
    lot: str = Query(""),
    spec: str = Query(""),
    brand: str = Query(""),
):
    rows = query_inventory(item_code=item_code, lot=lot, spec=spec)
    if brand:
        rows = [r for r in rows if (r.get("brand") or "") == brand]

    item_name = rows[0].get("item_name","") if rows else ""
    qr = build_item_qr(item_code, item_name, lot, spec, brand=brand or (rows[0].get("brand","") if rows else ""))

    return templates.TemplateResponse(
        "m/inventory_detail.html",
        {"request": request, "rows": rows, "item_code": item_code, "lot": lot, "spec": spec, "brand": brand, "qr": qr},
    )

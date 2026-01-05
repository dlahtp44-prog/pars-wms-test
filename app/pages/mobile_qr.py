from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ..core.paths import TEMPLATES_DIR
from ..utils.qr_format import parse_qr

router = APIRouter(prefix="/m/qr", tags=["mobile"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("", response_class=HTMLResponse)
def qr_home(request: Request, mode: str = "inventory"):
    return templates.TemplateResponse("m/qr_scan.html", {"request": request, "mode": mode})

@router.post("/submit")
def qr_submit(mode: str = Form("inventory"), raw: str = Form(...)):
    data = parse_qr(raw)
    warehouse = data.get("warehouse","MAIN")
    location = data.get("location","")
    if not location:
        return RedirectResponse(url="/m/qr?mode="+mode, status_code=302)
    if mode == "move":
        return RedirectResponse(url=f"/m/move/from?warehouse={warehouse}&from_location={location}", status_code=302)
    return RedirectResponse(url=f"/m/qr/inventory?warehouse={warehouse}&location={location}", status_code=302)

@router.get("/inventory", response_class=HTMLResponse)
def qr_inventory(request: Request, warehouse: str, location: str):
    return templates.TemplateResponse("m/qr_inventory.html", {"request": request, "warehouse": warehouse, "location": location})

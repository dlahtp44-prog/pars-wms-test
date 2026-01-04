from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.utils.qr_format import detect_qr_type, extract_item_fields, extract_location

router = APIRouter(prefix="/m/qr", tags=["mobile-qr"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
def qr_scan(request: Request):
    return templates.TemplateResponse("m/qr_scan.html", {"request": request})


@router.post("/submit")
def qr_submit(qrtext: str = Form(...)):
    qrtext = (qrtext or "").strip()

    qr_type = detect_qr_type(qrtext)

    if qr_type == "ITEM":
        item_code, item_name, lot, spec = extract_item_fields(qrtext)
        return RedirectResponse(
            url=f"/m/inventory/detail?item_code={item_code}&lot={lot}&spec={spec}",
            status_code=302
        )

    if qr_type == "LOCATION":
        loc = extract_location(qrtext) or qrtext
        return RedirectResponse(url=f"/m/qr/inventory?location={loc}", status_code=302)

    # UNKNOWN → 그냥 로케이션으로 한번 시도(현장 편의)
    return RedirectResponse(url=f"/m/qr/inventory?location={qrtext}", status_code=302)

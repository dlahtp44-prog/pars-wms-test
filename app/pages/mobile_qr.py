from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.paths import TEMPLATES_DIR
from app.utils.qr_format import is_item_qr, extract_item_fields

router = APIRouter(prefix="/m/qr", tags=["mobile-qr"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("", response_class=HTMLResponse)
def qr_scan(request: Request):
    return templates.TemplateResponse("m/qr_scan.html", {"request": request})

@router.post("/submit")
def qr_submit(qrtext: str = Form(...)):
    qrtext = (qrtext or "").strip()
    if is_item_qr(qrtext):
        item_code, item_name, lot, spec = extract_item_fields(qrtext)
        return RedirectResponse(url=f"/m/inventory/detail?item_code={item_code}&lot={lot}&spec={spec}", status_code=302)
    # 기본: 로케이션 코드로 간주
    return RedirectResponse(url=f"/m/qr/inventory?location={qrtext}", status_code=302)

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.utils.qr_format import is_item_qr, extract_item_fields

router = APIRouter(prefix="/m/qr", tags=["mobile-qr"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# QR 스캔 화면
@router.get("", response_class=HTMLResponse)
def qr_scan(request: Request, mode: str = ""):
    return templates.TemplateResponse(
        "m/qr_scan.html",
        {
            "request": request,
            "mode": mode,   # ← mode를 템플릿에 전달
        },
    )


# QR 처리
@router.post("/submit")
def qr_submit(
    qrtext: str = Form(...),
    mode: str = Form("")
):
    qrtext = (qrtext or "").strip()

    # 1️⃣ 품목 QR
    if is_item_qr(qrtext):
        item_code, item_name, lot, spec = extract_item_fields(qrtext)
        return RedirectResponse(
            url=f"/m/inventory/detail?item_code={item_code}&lot={lot}&spec={spec}",
            status_code=302,
        )

    # 2️⃣ 이동 모드 → 로케이션 이동
    if mode == "move":
        return RedirectResponse(
            url=f"/m/move?location={qrtext}",
            status_code=302,
        )

    # 3️⃣ 기본 → 로케이션 재고조회
    return RedirectResponse(
        url=f"/m/qr/inventory?location={qrtext}",
        status_code=302,
    )

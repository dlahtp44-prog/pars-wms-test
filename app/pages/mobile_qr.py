from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.utils.qr_format import parse_qr
from app.core.paths import TEMPLATES_DIR

router = APIRouter()

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/m/qr", response_class=HTMLResponse)
def qr_scan(request: Request, mode: str = "inventory", error: str = ""):
    # mode: inventory | move
    return templates.TemplateResponse(
        "m/qr_scan.html",
        {"request": request, "mode": mode, "error": error}
    )

@router.post("/m/qr/submit")
def qr_submit(
    request: Request,
    qr_raw: str = Form(...),
    warehouse: str = Form("MAIN"),
    mode: str = Form("inventory"),
):
    parsed = parse_qr(qr_raw)

    location = (parsed.get("location") or "").strip()
    # warehouse가 QR에 들어있으면 우선 사용
    qr_wh = (parsed.get("warehouse") or "").strip()
    if qr_wh:
        warehouse = qr_wh

    if not location:
        return RedirectResponse(url="/m/qr?error=invalid_qr", status_code=302)

    mode = (mode or "inventory").strip().lower()

    # ✅ 재고조회: 로케이션 재고 리스트
    if mode == "inventory":
        return RedirectResponse(
            url=f"/m/qr/inventory?warehouse={warehouse}&location={location}",
            status_code=302
        )

    # ✅ 이동: 출발 로케이션이 확정되면 품목 선택 화면으로 이동
    if mode == "move":
        return RedirectResponse(
            url=f"/m/move/select?from_location={location}",
            status_code=302
        )

    # 기타 모드 → 기본은 재고조회
    return RedirectResponse(
        url=f"/m/qr/inventory?warehouse={warehouse}&location={location}",
        status_code=302
    )

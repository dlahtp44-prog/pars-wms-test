from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.utils.qr_format import (
    is_item_qr,
    extract_item_fields,
    extract_location_only,
)

router = APIRouter(prefix="/m/qr", tags=["mobile-qr"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# =====================================================
# 📸 QR 스캔 화면
# =====================================================

@router.get("", response_class=HTMLResponse)
def qr_scan(request: Request, mode: str = ""):
    return templates.TemplateResponse(
        "m/qr_scan.html",
        {
            "request": request,
            "mode": mode,
        },
    )


# =====================================================
# ✅ QR 처리 (단일 진입점)
# =====================================================

@router.post("/submit")
def qr_submit(
    qrtext: str = Form(...),
    mode: str = Form("")
):
    qrtext = (qrtext or "").strip()
    if not qrtext:
        raise HTTPException(status_code=400, detail="QR 값이 비어 있습니다.")

    # 1️⃣ ITEM QR
    if is_item_qr(qrtext):
        if mode == "move":
            # ❌ 이동 모드에서는 ITEM QR 금지
            raise HTTPException(
                status_code=400,
                detail="이동은 로케이션 QR만 가능합니다.",
            )

        item_code, item_name, lot, spec = extract_item_fields(qrtext)
        return RedirectResponse(
            url=(
                f"/m/inventory/detail"
                f"?item_code={item_code}&lot={lot}&spec={spec}"
            ),
            status_code=303,
        )

    # 2️⃣ LOCATION QR
    location = extract_location_only(qrtext)
    if not location:
        raise HTTPException(status_code=400, detail="로케이션 QR이 아닙니다.")

    # 안전 검증 (이중 방어)
    if any(x in location for x in ["&", "?", "="]):
        raise HTTPException(
            status_code=400,
            detail="잘못된 로케이션 QR 형식입니다.",
        )

    # 3️⃣ 이동 모드
    if mode == "move":
        return RedirectResponse(
            url=f"/m/move/from?location={location}",
            status_code=303,
        )

    # 4️⃣ 기본 → 로케이션 재고 조회
    return RedirectResponse(
        url=f"/m/qr/inventory?location={location}",
        status_code=303,
    )

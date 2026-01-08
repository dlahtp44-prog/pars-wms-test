from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/m/move", tags=["mobile-move"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# =====================================================
# 유틸: 로케이션 값 검증
# =====================================================

def _validate_location(raw: str) -> str:
    """
    ✅ QR 이동용 로케이션 검증
    - &, ?, = 포함 시 → QR ITEM 으로 판단 → 차단
    - 공백 제거
    """
    loc = (raw or "").strip()
    if not loc:
        raise HTTPException(status_code=400, detail="로케이션 값이 비어 있습니다.")

    if any(x in loc for x in ["&", "?", "="]):
        raise HTTPException(
            status_code=400,
            detail="QR 재고 이동은 로케이션 QR만 가능합니다.",
        )

    return loc


# =====================================================
# 1️⃣ 출발 로케이션 화면
# =====================================================

@router.get("/from", response_class=HTMLResponse)
def move_from(request: Request, location: str):
    """
    QR 스캔 → 출발 로케이션 입력 화면
    """
    from_location = _validate_location(location)

    return templates.TemplateResponse(
        "m/move_from.html",
        {
            "request": request,
            "from_location": from_location,
        },
    )


# =====================================================
# 2️⃣ 출발 로케이션 확정
# =====================================================

@router.post("/from/submit")
def move_from_submit(from_location: str = Form(...)):
    """
    출발 로케이션 확정 → 품목 선택 단계로 이동
    """
    from_location = _validate_location(from_location)

    return RedirectResponse(
        url=f"/m/move/select?from_location={from_location}",
        status_code=303,
    )

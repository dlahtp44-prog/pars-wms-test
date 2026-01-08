from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import re

from app.core.paths import TEMPLATES_DIR

router = APIRouter(prefix="/m/move", tags=["mobile-move"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# =====================================================
# 유틸: 로케이션 값 검증
# =====================================================

_LOC_RE = re.compile(r"^[A-Za-z0-9\-_/]+$")

def _validate_location(raw: str) -> str:
    """
    ✅ QR 이동용 로케이션 검증
    - ITEM QR / 쿼리스트링 차단
    - 길이 / 형식 제한
    """
    loc = (raw or "").strip()

    if not loc:
        return ""

    # ITEM QR / 쿼리 형태 차단
    if any(x in loc for x in ["&", "?", "="]):
        return ""

    if len(loc) > 60:
        return ""

    if not _LOC_RE.match(loc):
        return ""

    return loc


# =====================================================
# 1️⃣ 출발 로케이션 화면
# =====================================================

@router.get("/from", response_class=HTMLResponse)
def move_from(
    request: Request,
    location: str = "",
    warehouse: str = "",
):
    """
    QR 스캔 → 출발 로케이션 입력 화면
    """
    from_location = _validate_location(location)

    if not from_location:
        return templates.TemplateResponse(
            "m/move_from.html",
            {
                "request": request,
                "from_location": "",
                "warehouse": warehouse,
                "msg": "로케이션 QR이 올바르지 않습니다.",
            },
        )

    return templates.TemplateResponse(
        "m/move_from.html",
        {
            "request": request,
            "from_location": from_location,
            "warehouse": warehouse,
            "msg": "",
        },
    )


# =====================================================
# 2️⃣ 출발 로케이션 확정
# =====================================================

@router.post("/from/submit")
def move_from_submit(
    from_location: str = Form(...),
    warehouse: str = Form(""),
):
    """
    출발 로케이션 확정 → 품목 선택 단계로 이동
    """
    fl = _validate_location(from_location)

    if not fl:
        return RedirectResponse(
            url="/m/move/from?error=invalid_location",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/m/move/select?from_location={fl}&warehouse={warehouse}",
        status_code=303,
    )

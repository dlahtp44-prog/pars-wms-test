from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from app.utils.qr_format import parse_qr

router = APIRouter()

@router.post("/m/qr/submit")
def qr_submit(
    request: Request,
    qr_raw: str = Form(...),
    warehouse: str = Form("MAIN"),
    mode: str = Form("inventory"),
):
    parsed = parse_qr(qr_raw)

    # ✅ 핵심 수정: location 문자열만 정확히 추출
    location = None

    if isinstance(parsed, dict):
        # 표준 QR
        if parsed.get("type") in ("LOC", "LOCATION"):
            location = parsed.get("location")

        # fallback (혹시라도 location 키만 있는 경우)
        if not location:
            location = parsed.get("location")

    # ❌ location 없으면 에러
    if not location:
        return RedirectResponse(
            url="/m/qr?error=invalid_qr",
            status_code=302
        )

    # ✅ 정상 이동
    return RedirectResponse(
        url=f"/m/qr/inventory?warehouse={warehouse}&location={location}",
        status_code=302
    )

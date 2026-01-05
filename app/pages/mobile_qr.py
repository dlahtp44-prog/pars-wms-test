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

    # 🔥 핵심: dict 전체 ❌, location 값만 사용
    location = parsed.get("location")

    if not location:
        return RedirectResponse(
            url="/m/qr?error=invalid_qr",
            status_code=302
        )

    return RedirectResponse(
        url=f"/m/qr/inventory?warehouse={warehouse}&location={location}",
        status_code=302
    )

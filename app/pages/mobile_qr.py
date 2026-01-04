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
    """
    QR 스캔 submit 처리
    - 이동(mode=move)
    - 재고조회(mode=inventory)
    """

    parsed = parse_qr(qr_raw)

    # 🔥 핵심 수정 포인트
    location = parsed.get("location")

    if not location:
        # QR 파싱 실패 시 다시 QR 페이지로
        return RedirectResponse(
            url="/m/qr?error=invalid_qr",
            status_code=302
        )

    # 이동 모드
    if mode == "move":
        return RedirectResponse(
            url=f"/m/qr/inventory?warehouse={warehouse}&location={location}",
            status_code=302
        )

    # 기본: 재고 조회
    return RedirectResponse(
        url=f"/m/qr/inventory?warehouse={warehouse}&location={location}",
        status_code=302
    )

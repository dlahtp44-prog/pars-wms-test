from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.utils.qr_format import parse_qr

router = APIRouter()

@router.post("/m/qr/submit")
async def qr_submit(
    request: Request,
    qr: str = Form(...)
):
    data = parse_qr(qr)

    qr_type = data.get("type", "").upper()

    # 로케이션 QR
    if qr_type in ["LOC", "LOCATION"]:
        warehouse = data.get("warehouse", "MAIN")
        location = data.get("location")

        return RedirectResponse(
            url=f"/m/qr/inventory?warehouse={warehouse}&location={location}",
            status_code=302
        )

    # 품목 QR (확장 대비)
    if qr_type in ["ITEM", "PRODUCT"]:
        item_code = data.get("code")
        lot = data.get("lot")
        spec = data.get("spec")

        return RedirectResponse(
            url=f"/m/item?item_code={item_code}&lot={lot}&spec={spec}",
            status_code=302
        )

    # 알 수 없는 QR
    return RedirectResponse("/m/qr", status_code=302)

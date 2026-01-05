parsed = parse_qr(qr_raw)

location = parsed.get("location")
item_code = parsed.get("item_code")
lot = parsed.get("lot")

# LOCATION QR → 재고 조회
if location and mode == "inventory":
    return RedirectResponse(
        url=f"/m/qr/inventory?warehouse={warehouse}&location={location}",
        status_code=302
    )

# ITEM QR → 이동 화면
if item_code and lot:
    return RedirectResponse(
        url=f"/m/move?warehouse={warehouse}&item_code={item_code}&lot={lot}",
        status_code=302
    )

return RedirectResponse(
    url="/m/qr?error=invalid_qr",
    status_code=302
)

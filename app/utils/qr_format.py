from urllib.parse import parse_qs

# =========================
# QR TYPE 판별
# =========================
def detect_qr_type(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return "UNKNOWN"

    if "item_code=" in raw or "ITEM" in raw.upper():
        return "ITEM"

    if "location=" in raw or raw.replace("-", "").isalnum():
        return "LOCATION"

    return "UNKNOWN"


# =========================
# QR 파싱 (v1.6 안정판)
# =========================
def parse_qr(raw: str) -> dict:
    raw = (raw or "").strip()
    if not raw:
        return {}

    # querystring 형태
    if "=" in raw:
        qs = parse_qs(raw, keep_blank_values=True)
        result = {
            k.lower(): (v[0] if isinstance(v, list) and v else v)
            for k, v in qs.items()
        }
        result.pop("type", None)  # 사고 방지
        return result

    # 그냥 로케이션만 있는 경우
    return {"location": raw}


# =========================
# LOCATION 추출
# =========================
def extract_location(raw: str) -> str | None:
    data = parse_qr(raw)
    return data.get("location")


# =========================
# ITEM 필드 추출
# =========================
def extract_item_fields(raw: str):
    data = parse_qr(raw)
    return (
        data.get("item_code", ""),
        data.get("item_name", ""),
        data.get("lot", ""),
        data.get("spec", ""),
    )


# =========================
# ITEM QR 생성
# =========================
def build_item_qr(
    warehouse: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
) -> str:
    return (
        f"type=ITEM"
        f"&warehouse={warehouse}"
        f"&item_code={item_code}"
        f"&item_name={item_name}"
        f"&lot={lot}"
        f"&spec={spec}"
    )

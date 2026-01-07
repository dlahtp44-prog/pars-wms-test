import re
from urllib.parse import unquote_plus

# =========================
# 품목 QR 판별
# =========================
def is_item_qr(text: str) -> bool:
    if not text:
        return False
    return ("품번:" in text) and ("LOT:" in text)

# =========================
# 품목 QR 필드 추출
# =========================
def extract_item_fields(text: str):
    def pick(label: str) -> str:
        m = re.search(rf"{re.escape(label)}\s*:\s*([^/]+)", text)
        return m.group(1).strip() if m else ""
    return (
        pick("품번"),
        pick("품명"),
        pick("LOT"),
        pick("규격"),
    )

# =========================
# 로케이션 QR → location 값만 추출
# =========================
def extract_location_only(text: str) -> str:
    """
    허용 포맷:
    - D01-01
    - B01-02-A
    - type=LOC&warehouse=MAIN&location=D01-01

    차단:
    - type=ITEM...
    - 품번:xxx/LOT:xxx
    """
    if not text:
        return ""

    t = text.strip()

    # URL 인코딩된 값일 수 있어 한 번 풀어줌
    try:
        t = unquote_plus(t)
    except Exception:
        pass

    # ITEM QR 차단
    if is_item_qr(t):
        return ""
    if "type=ITEM" in t:
        return ""

    # URL 파라미터에서 location 추출
    if "location=" in t:
        v = t.split("location=")[-1]
        v = v.split("&")[0].strip()
        return v

    # 순수 로케이션 패턴만 허용 (예: D01-01, B01-02-A)
    m = re.fullmatch(r"[A-Z]\d{2}-\d{2}(-[A-Z])?", t)
    return m.group(0) if m else ""

# =========================
# 품목 QR 생성
# =========================
def build_item_qr(
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    brand: str | None = None,
) -> str:
    qr = (
        f"품번:{item_code}/"
        f"품명:{item_name}/"
        f"LOT:{lot}/"
        f"규격:{spec}"
    )
    if brand:
        qr += f"/브랜드:{brand}"
    return qr

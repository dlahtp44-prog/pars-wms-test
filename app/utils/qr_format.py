# app/utils/qr_format.py
import re

# =========================
# 품목 QR 판별
# =========================
def is_item_qr(text: str) -> bool:
    if not text:
        return False
    return "품번:" in text and "LOT:" in text


# =========================
# 품목 QR 필드 추출
# =========================
def extract_item_fields(text: str):
    def pick(label):
        m = re.search(rf"{label}\s*:\s*([^/]+)", text)
        return m.group(1).strip() if m else ""

    return (
        pick("품번"),
        pick("품명"),
        pick("LOT"),
        pick("규격"),
    )


# =========================
# 로케이션 QR → location 값만 추출 (★단일 정의★)
# =========================
def extract_location_only(text: str) -> str:
    """
    허용:
    - D01-01
    - B01-02-A
    - type=LOC&warehouse=MAIN&location=D01-01

    차단:
    - ITEM QR
    - type=ITEM
    """

    if not text:
        return ""

    text = text.strip()

    # ❌ ITEM QR 차단
    if is_item_qr(text):
        return ""

    if "type=ITEM" in text:
        return ""

    # URL 파라미터
    if "location=" in text:
        value = text.split("location=")[-1]
        return value.split("&")[0].strip()

    # 순수 로케이션 패턴
    m = re.fullmatch(r"[A-Z]\d{2}-\d{2}(-[A-Z])?", text)
    return m.group(0) if m else ""


# =========================
# ✅ 품목 QR 생성 (mobile_inventory_detail 필수)
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

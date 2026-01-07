# app/utils/qr_format.py
import re


# =========================
# ITEM QR 판별
# =========================
def is_item_qr(text: str) -> bool:
    if not text:
        return False
    return "품번:" in text and "LOT:" in text


# =========================
# ITEM QR 필드 추출
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
# 🔑 로케이션 QR만 허용
# =========================
def extract_location_only(text: str) -> str:
    if not text:
        return ""

    text = text.strip()

    # ❌ ITEM QR 차단
    if is_item_qr(text):
        return ""

    # ❌ ITEM URL 차단
    if "type=ITEM" in text:
        return ""

    # URL 파라미터 방식
    if "location=" in text:
        value = text.split("location=")[-1]
        value = value.split("&")[0].strip()
        return value

    # 순수 로케이션 패턴만 허용
    m = re.fullmatch(r"[A-Z]\d{2}-\d{2}(-[A-Z])?", text)
    return m.group(0) if m else ""

# app/utils/qr_format.py

import re

# =========================
# 품목 QR 판별
# =========================
def is_item_qr(text: str) -> bool:
    return "품번" in text and "LOT" in text


# =========================
# 품목 QR 필드 추출
# =========================
def extract_item_fields(text: str):
    def pick(label):
        m = re.search(rf"{label}\s*:\s*([^\n/]+)", text)
        return m.group(1).strip() if m else ""

    item_code = pick("품번")
    item_name = pick("품명")
    lot = pick("LOT")
    spec = pick("규격")

    return item_code, item_name, lot, spec


# =========================
# 로케이션 QR → location 값만 추출
# =========================
def extract_location_only(text: str) -> str:
    """
    예:
    type=LOC&warehouse=MAIN&location=D01-01
    → D01-01
    """
    if "location=" in text:
        return text.split("location=")[-1].strip()
    return text.strip()


# =========================
# ✅ 품목 QR 생성 (v1.8 기준 단일 포맷)
# =========================
def build_item_qr(
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    brand: str | None = None,
) -> str:
    """
    QR 포함 필드:
    - 품번
    - 품명
    - LOT
    - 규격
    - 브랜드(선택)
    """

    qr = (
        f"품번:{item_code}/"
        f"품명:{item_name}/"
        f"LOT:{lot}/"
        f"규격:{spec}"
    )

    if brand:
        qr += f"/브랜드:{brand}"

    return qr

import re


def is_item_qr(text: str) -> bool:
    return "품번" in text and "LOT" in text


def extract_item_fields(text: str):
    def pick(label):
        m = re.search(rf"{label}\s*:\s*([^\n/]+)", text)
        return m.group(1).strip() if m else ""

    return (
        pick("품번"),
        pick("품명"),
        pick("LOT"),
        pick("규격"),
    )


# ✅ 핵심 함수
def extract_location_only(text: str) -> str:
    """
    type=LOC&warehouse=MAIN&location=D01-01
    → D01-01
    """
    if "location=" in text:
        return text.split("location=")[-1].strip()

    return text.strip()

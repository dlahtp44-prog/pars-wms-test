def parse_qr(raw: str) -> dict:
    """
    QR 문자열 예:
    type=LOC&warehouse=MAIN&location=D01-01
    """

    result = {}

    if not raw:
        return result

    raw = raw.strip()
    parts = raw.split("&")

    for part in parts:
        if "=" not in part:
            continue

        key, value = part.split("=", 1)
        key = key.strip().lower()
        value = value.strip()

        # type은 제거 (location 오염 방지)
        if key == "type":
            continue

        result[key] = value

    return result

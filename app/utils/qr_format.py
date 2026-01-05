def parse_qr(raw: str) -> dict:
    """
    QR 문자열 예:
    type=LOC&warehouse=MAIN&location=D01-01
    """

    result = {}

    if not raw:
        return result

    parts = raw.split("&")

    for part in parts:
        if "=" not in part:
            continue

        key, value = part.split("=", 1)

        # ❌ type은 버린다
        if key.lower() == "type":
            continue

        result[key.lower()] = value

    return result

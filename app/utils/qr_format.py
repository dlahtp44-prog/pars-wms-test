from urllib.parse import parse_qs, quote, unquote

def parse_qr(raw: str) -> dict:
    """PARS WMS QR parser (v1.6 안정판)

    지원 입력 예:
    - "type=LOC&warehouse=MAIN&location=D01-01"
    - "warehouse=MAIN&location=D01-01"
    - "D01-01"  (로케이션만 있는 경우)

    반환:
    - {"warehouse": "...", "location": "..."} 중심
    """
    raw = (raw or "").strip()
    if not raw:
        return {}

    # querystring 형태
    if "=" in raw and "&" in raw:
        qs = parse_qs(raw, keep_blank_values=True)
        result = {k.lower(): (v[0] if isinstance(v, list) and v else v) for k, v in qs.items()}
        # 사고 방지: type 제거
        result.pop("type", None)
        # url-encoding 복원
        for k in list(result.keys()):
            if isinstance(result[k], str):
                result[k] = unquote(result[k])
        return result

    # 단일 key=value
    if "=" in raw and "&" not in raw:
        k, v = raw.split("=", 1)
        k = k.strip().lower()
        v = unquote(v.strip())
        if k == "type":
            return {}
        return {k: v}

    # 그냥 로케이션
    return {"location": raw}

def build_location_qr(warehouse: str, location: str) -> str:
    return f"type=LOC&warehouse={quote(str(warehouse))}&location={quote(str(location))}"

def build_item_qr(warehouse: str, item_code: str, item_name: str, lot: str, spec: str) -> str:
    return (
        f"type=ITEM"
        f"&warehouse={quote(str(warehouse))}"
        f"&item_code={quote(str(item_code))}"
        f"&item_name={quote(str(item_name))}"
        f"&lot={quote(str(lot))}"
        f"&spec={quote(str(spec))}"
    )

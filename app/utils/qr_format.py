from urllib.parse import parse_qs


def parse_qr(raw: str) -> dict:
    """
    PARS WMS QR 파서 (v1.6 안정판)

    지원 입력 예:
    - "type=LOC&warehouse=MAIN&location=D01-01"
    - "warehouse=MAIN&location=D01-01"
    - "D01-01"  (로케이션만 있는 경우)

    반환:
    - {"warehouse": "...", "location": "..."} 중심으로 반환
    """
    raw = (raw or "").strip()
    if not raw:
        return {}

    # 1) querystring 형태 (&, =) 인 경우
    if "=" in raw and "&" in raw:
        qs = parse_qs(raw, keep_blank_values=True)
        result = {
            k.lower(): (v[0] if isinstance(v, list) and v else v)
            for k, v in qs.items()
        }
        # type은 제거 (location 값에 섞여 들어가는 사고 방지)
        result.pop("type", None)
        return result

    # 2) "=" 포함하지만 "&"는 없는 경우
    if "=" in raw and "&" not in raw:
        k, v = raw.split("=", 1)
        k = k.strip().lower()
        v = v.strip()
        if k == "type":
            return {}
        return {k: v}

    # 3) 그냥 로케이션 문자열만 들어온 경우
    return {"location": raw}


def build_item_qr(
    warehouse: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
) -> str:
    """
    ITEM QR 문자열 생성 (모바일/라벨 공용)
    """
    return (
        f"type=ITEM"
        f"&warehouse={warehouse}"
        f"&item_code={item_code}"
        f"&item_name={item_name}"
        f"&lot={lot}"
        f"&spec={spec}"
    )

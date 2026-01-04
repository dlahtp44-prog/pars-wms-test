from __future__ import annotations

from typing import Dict, Tuple, Literal, Optional

# =========================
# QR Payload Standard (v1)
# =========================
# 권장 포맷(1줄):
#   PARS|TYPE=LOCATION|CODE=D01-01
#   PARS|TYPE=ITEM|CODE=728752|NAME=Walks/1.0 Gray SOFT|LOT=H48N5|SPEC=600*600*9
#
# - 구분자: '|' (권장) / '&' / '\n' 모두 허용
# - 키 대소문자 무시, 한국어 레거시("품번=...")도 계속 지원
#
# 참고: 스캐너/카메라에 따라 공백/개행이 섞여 들어올 수 있으므로 최대한 관대하게 파싱합니다.

QR_ITEM_KEYS_LEGACY = ["품번", "품명", "LOT", "규격"]

QrType = Literal["LOCATION", "ITEM", "UNKNOWN"]

def _split_tokens(text: str) -> list[str]:
    t = (text or "").strip()
    if not t:
        return []
    # 표준 구분자 우선
    if "|" in t:
        return [x.strip() for x in t.split("|") if x.strip()]
    if "&" in t:
        return [x.strip() for x in t.split("&") if x.strip()]
    # 레거시(줄바꿈)
    return [x.strip() for x in t.splitlines() if x.strip()]

def parse_kv(text: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for token in _split_tokens(text):
        if token.upper() == "PARS":
            data["_PARS"] = "1"
            continue
        if "=" in token:
            k, v = token.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k:
                data[k] = v
    return data

def detect_qr_type(text: str) -> QrType:
    d = parse_kv(text)
    # 표준
    t = (d.get("TYPE") or d.get("type") or "").strip().upper()
    if t in ("LOCATION", "ITEM"):
        return t  # type: ignore[return-value]

    # 레거시 ITEM
    if all((k in d and d[k]) for k in QR_ITEM_KEYS_LEGACY):
        return "ITEM"

    # 레거시 LOCATION: 단일 코드만 들어오는 경우가 많음
    raw = (text or "").strip()
    if raw and ("=" not in raw) and (len(raw) <= 40):
        return "LOCATION"

    return "UNKNOWN"

def build_location_qr(code: str) -> str:
    code = (code or "").strip()
    return f"PARS|TYPE=LOCATION|CODE={code}"

def build_item_qr(item_code: str, item_name: str, lot: str, spec: str) -> str:
    # 표준 포맷(권장)
    return "PARS|TYPE=ITEM|" + "|".join([
        f"CODE={_escape(item_code)}",
        f"NAME={_escape(item_name)}",
        f"LOT={_escape(lot)}",
        f"SPEC={_escape(spec)}",
    ])

def build_item_qr_legacy(item_code: str, item_name: str, lot: str, spec: str) -> str:
    # 기존(줄바꿈) 포맷도 유지
    return "\n".join([
        f"품번={item_code}",
        f"품명={item_name}",
        f"LOT={lot}",
        f"규격={spec}",
    ])

def _escape(v: str) -> str:
    # QR에 구분자(|)가 들어가면 파싱이 깨지므로 간단 치환
    return (v or "").replace("|", "/").strip()

def extract_location(text: str) -> Optional[str]:
    d = parse_kv(text)
    # 표준
    for k in ("CODE", "code", "LOCATION", "location"):
        if d.get(k):
            return d[k].strip()
    # 레거시: raw string 자체
    raw = (text or "").strip()
    if raw and ("=" not in raw) and (len(raw) <= 40):
        return raw
    return None

def extract_item_fields(text: str) -> Tuple[str, str, str, str]:
    d = parse_kv(text)
    # 표준
    code = d.get("CODE") or d.get("code") or ""
    name = d.get("NAME") or d.get("name") or ""
    lot = d.get("LOT") or d.get("lot") or ""
    spec = d.get("SPEC") or d.get("spec") or ""
    if code and lot and spec:
        return code.strip(), name.strip(), lot.strip(), spec.strip()

    # 레거시
    return (
        (d.get("품번") or "").strip(),
        (d.get("품명") or "").strip(),
        (d.get("LOT") or "").strip(),
        (d.get("규격") or "").strip(),
    )

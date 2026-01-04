from __future__ import annotations
from typing import Dict, Tuple, Literal, Optional

QR_ITEM_KEYS_LEGACY = ["품번", "품명", "LOT", "규격"]
QrType = Literal["LOCATION", "ITEM", "UNKNOWN"]

def _split_tokens(text: str) -> list[str]:
    t = (text or "").strip()
    if not t:
        return []
    if "|" in t:
        return [x.strip() for x in t.split("|") if x.strip()]
    if "&" in t:
        return [x.strip() for x in t.split("&") if x.strip()]
    return [x.strip() for x in t.splitlines() if x.strip()]

def parse_kv(text: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for token in _split_tokens(text):
        if token.upper() == "PARS":
            continue
        if "=" in token:
            k, v = token.split("=", 1)
            data[k.strip().upper()] = v.strip()
    return data

def detect_qr_type(text: str) -> QrType:
    d = parse_kv(text)
    t = d.get("TYPE", "").upper()
    if t in ("LOCATION", "ITEM"):
        return t
    if all((k in d and d[k]) for k in QR_ITEM_KEYS_LEGACY):
        return "ITEM"
    raw = (text or "").strip()
    if raw and ("=" not in raw) and len(raw) <= 40:
        return "LOCATION"
    return "UNKNOWN"

def extract_location(text: str) -> Optional[str]:
    d = parse_kv(text)
    for k in ("CODE", "LOCATION"):
        if d.get(k):
            return d[k]
    raw = (text or "").strip()
    if raw and ("=" not in raw) and len(raw) <= 40:
        return raw
    return None

def extract_item_fields(text: str) -> Tuple[str, str, str, str]:
    d = parse_kv(text)
    code = d.get("CODE", "")
    name = d.get("NAME", "")
    lot = d.get("LOT", "")
    spec = d.get("SPEC", "")
    if code and lot and spec:
        return code, name, lot, spec
    return (
        d.get("품번", ""),
        d.get("품명", ""),
        d.get("LOT", ""),
        d.get("규격", ""),
    )

def parse_qr(raw: str) -> dict:
    raw = (raw or "").strip()
    if not raw:
        return {"type": "UNKNOWN"}
    qr_type = detect_qr_type(raw)
    if qr_type == "LOCATION":
        return {"type": "LOCATION", "location": extract_location(raw)}
    if qr_type == "ITEM":
        code, name, lot, spec = extract_item_fields(raw)
        return {
            "type": "ITEM",
            "item_code": code,
            "item_name": name,
            "lot": lot,
            "spec": spec,
        }
    return {"type": "UNKNOWN"}

from typing import Dict, Tuple

QR_KEYS = ["품번","품명","LOT","규격"]

def build_item_qr(item_code: str, item_name: str, lot: str, spec: str) -> str:
    # 표준 포맷: key=value per line
    return "\n".join([
        f"품번={item_code}",
        f"품명={item_name}",
        f"LOT={lot}",
        f"규격={spec}",
    ])

def parse_qr(text: str) -> Dict[str, str]:
    text = (text or "").strip()
    data: Dict[str,str] = {}
    for line in text.splitlines():
        if "=" in line:
            k,v = line.split("=",1)
            k=k.strip()
            v=v.strip()
            if k:
                data[k]=v
    return data

def is_item_qr(text: str) -> bool:
    d=parse_qr(text)
    return all(k in d and d[k] for k in QR_KEYS)

def extract_item_fields(text: str) -> Tuple[str,str,str,str]:
    d=parse_qr(text)
    return d.get("품번",""), d.get("품명",""), d.get("LOT",""), d.get("규격","")

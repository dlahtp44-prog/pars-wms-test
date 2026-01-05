from urllib.parse import parse_qs, urlencode
def parse_qr(raw:str)->dict:
    raw=(raw or "").strip()
    if not raw: return {}
    if "=" in raw and "&" in raw:
        qs=parse_qs(raw, keep_blank_values=True)
        result={k.lower():(v[0] if isinstance(v,list) and v else v) for k,v in qs.items()}
        result.pop("type",None)
        return result
    if "=" in raw and "&" not in raw:
        k,v=raw.split("=",1);k=k.strip().lower();v=v.strip()
        if k=="type": return {}
        return {k:v}
    return {"location":raw}
def build_item_qr(warehouse,item_code,item_name,lot,spec)->str:
    return urlencode({"type":"ITEM","warehouse":warehouse,"item_code":item_code,"item_name":item_name,"lot":lot,"spec":spec})

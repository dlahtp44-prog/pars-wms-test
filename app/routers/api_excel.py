from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from openpyxl import load_workbook
from ..db import get_db
from .api_inventory import upsert_inventory, add_history

router = APIRouter(prefix="/api/excel", tags=["excel"])

REQUIRED_COMMON = ["로케이션", "품번", "품명", "LOT", "규격", "수량"]

def _norm(s: str) -> str:
    return (s or "").strip()

def _read_rows(file: UploadFile):
    wb = load_workbook(file.file, data_only=True)
    ws = wb.active
    headers = []
    for cell in ws[1]:
        headers.append(_norm(cell.value))
    idx = {h: i for i, h in enumerate(headers)}
    rows=[]
    for r in ws.iter_rows(min_row=2, values_only=True):
        if all(v is None or str(v).strip()=="" for v in r):
            continue
        row={h: r[idx[h]] if h in idx else None for h in headers}
        rows.append(row)
    return headers, rows

def _get(row, key):
    v=row.get(key)
    return "" if v is None else str(v).strip()

def _get_int(row, key):
    v=row.get(key)
    try:
        return int(float(v))
    except Exception:
        return 0

@router.post("/inbound")
async def excel_inbound(file: UploadFile = File(...), warehouse_default: str = Form("MAIN"), operator: str = Form(""), note: str = Form("")):
    headers, rows = _read_rows(file)
    missing=[h for h in REQUIRED_COMMON if h not in headers]
    if missing:
        return JSONResponse(status_code=400, content={"ok": False, "detail": f"필수 컬럼 누락: {', '.join(missing)}"})
    ok=0
    with get_db() as conn:
        for row in rows:
            wh = _get(row,"창고") or warehouse_default
            loc=_get(row,"로케이션")
            item_code=_get(row,"품번")
            item_name=_get(row,"품명")
            lot=_get(row,"LOT")
            spec=_get(row,"규격")
            qty=_get_int(row,"수량")
            brand=_get(row,"브랜드")
            rnote=_get(row,"비고") or note
            if not (loc and item_code and item_name and qty>0):
                continue
            upsert_inventory(conn, warehouse=wh, location=loc, brand=brand, item_code=item_code, item_name=item_name, lot=lot, spec=spec, delta_qty=qty, note=rnote)
            add_history(conn, type="INBOUND", warehouse=wh, location=loc, brand=brand, item_code=item_code, item_name=item_name, lot=lot, spec=spec, qty=qty, note=rnote, operator=operator)
            ok += 1
    return {"ok": True, "count": ok}

@router.post("/outbound")
async def excel_outbound(file: UploadFile = File(...), warehouse_default: str = Form("MAIN"), operator: str = Form(""), note: str = Form("")):
    headers, rows = _read_rows(file)
    missing=[h for h in REQUIRED_COMMON if h not in headers]
    if missing:
        return JSONResponse(status_code=400, content={"ok": False, "detail": f"필수 컬럼 누락: {', '.join(missing)}"})
    ok=0
    with get_db() as conn:
        for row in rows:
            wh = _get(row,"창고") or warehouse_default
            loc=_get(row,"로케이션")
            item_code=_get(row,"품번")
            item_name=_get(row,"품명")
            lot=_get(row,"LOT")
            spec=_get(row,"규격")
            qty=_get_int(row,"수량")
            brand=_get(row,"브랜드")
            rnote=_get(row,"비고") or note
            if not (loc and item_code and item_name and qty>0):
                continue
            upsert_inventory(conn, warehouse=wh, location=loc, brand=brand, item_code=item_code, item_name=item_name, lot=lot, spec=spec, delta_qty=-qty, note=rnote)
            add_history(conn, type="OUTBOUND", warehouse=wh, location=loc, brand=brand, item_code=item_code, item_name=item_name, lot=lot, spec=spec, qty=qty, note=rnote, operator=operator)
            ok += 1
    return {"ok": True, "count": ok}

@router.post("/move")
async def excel_move(file: UploadFile = File(...), warehouse_default: str = Form("MAIN"), operator: str = Form(""), note: str = Form("")):
    # 필요 컬럼: 출발, 도착, 품번, 품명, LOT, 규격, 수량
    required = ["출발", "도착", "품번", "품명", "LOT", "규격", "수량"]
    headers, rows = _read_rows(file)
    missing=[h for h in required if h not in headers]
    if missing:
        return JSONResponse(status_code=400, content={"ok": False, "detail": f"필수 컬럼 누락: {', '.join(missing)}"})
    ok=0
    with get_db() as conn:
        for row in rows:
            wh = _get(row,"창고") or warehouse_default
            from_loc=_get(row,"출발")
            to_loc=_get(row,"도착")
            item_code=_get(row,"품번")
            item_name=_get(row,"품명")
            lot=_get(row,"LOT")
            spec=_get(row,"규격")
            qty=_get_int(row,"수량")
            brand=_get(row,"브랜드")
            rnote=_get(row,"비고") or note
            if not (from_loc and to_loc and item_code and item_name and qty>0):
                continue
            upsert_inventory(conn, warehouse=wh, location=from_loc, brand=brand, item_code=item_code, item_name=item_name, lot=lot, spec=spec, delta_qty=-qty, note=rnote)
            upsert_inventory(conn, warehouse=wh, location=to_loc, brand=brand, item_code=item_code, item_name=item_name, lot=lot, spec=spec, delta_qty=qty, note=rnote)
            add_history(conn, type="MOVE", warehouse=wh, from_location=from_loc, to_location=to_loc, brand=brand, item_code=item_code, item_name=item_name, lot=lot, spec=spec, qty=qty, note=rnote, operator=operator)
            ok += 1
    return {"ok": True, "count": ok}

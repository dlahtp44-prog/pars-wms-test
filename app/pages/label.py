from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import io
from app.core.paths import TEMPLATES_DIR

router = APIRouter(
    prefix="/label",
    tags=["라벨출력"],
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# =====================================================
# LOCATION LABEL
# =====================================================

@router.get("/location/excel", response_class=HTMLResponse)
@router.get("/로케이션/excel", response_class=HTMLResponse)
def label_location_excel_form(request: Request):
    return templates.TemplateResponse(
        "label_location_excel_form.html",
        {"request": request},
    )


@router.post("/location/excel/preview", response_class=HTMLResponse)
@router.post("/로케이션/excel/preview", response_class=HTMLResponse)
async def label_location_excel_preview(
    request: Request,
    file: UploadFile = File(...),
    size: str = Form("70x40"),
    qty: int = Form(1),
):
    df = pd.read_excel(io.BytesIO(await file.read()))
    df.columns = [c.lower().strip() for c in df.columns]

    if "location" not in df.columns:
        return HTMLResponse("엑셀에 location 컬럼이 없습니다", status_code=400)

    locations = df["location"].dropna().astype(str).tolist()

    return templates.TemplateResponse(
        "label_location_excel_preview.html",
        {
            "request": request,
            "locations": locations,
            "size": size,
            "qty": qty,
        },
    )


@router.post("/location/excel/print", response_class=HTMLResponse)
@router.post("/로케이션/excel/print", response_class=HTMLResponse)
def label_location_excel_print(
    request: Request,
    locations: list[str] = Form(...),
    size: str = Form(...),
    qty: int = Form(...),
):
    w, h = map(int, size.split("x"))
    return templates.TemplateResponse(
        "label_location_excel_print.html",
        {
            "request": request,
            "locations": locations,
            "qty": qty,
            "width_mm": w,
            "height_mm": h,
        },
    )


# =====================================================
# ITEM LABEL
# =====================================================

@router.get("/item/excel", response_class=HTMLResponse)
@router.get("/제품/excel", response_class=HTMLResponse)
def label_item_excel_form(request: Request):
    return templates.TemplateResponse(
        "label_item_excel_form.html",
        {"request": request},
    )


@router.post("/item/excel/preview", response_class=HTMLResponse)
@router.post("/제품/excel/preview", response_class=HTMLResponse)
async def label_item_excel_preview(
    request: Request,
    file: UploadFile = File(...),
    size: str = Form("70x40"),
    qty: int = Form(1),
):
    df = pd.read_excel(io.BytesIO(await file.read()))
    df.columns = [c.lower().strip() for c in df.columns]

    required = {"code", "name", "lot", "spec"}
    if not required.issubset(df.columns):
        return HTMLResponse("code, name, lot, spec 컬럼 필요", status_code=400)

    items = df[list(required)].dropna().to_dict(orient="records")

    return templates.TemplateResponse(
        "label_item_excel_preview.html",
        {
            "request": request,
            "items": items,
            "size": size,
            "qty": qty,
        },
    )


@router.post("/item/excel/print", response_class=HTMLResponse)
@router.post("/제품/excel/print", response_class=HTMLResponse)
def label_item_excel_print(
    request: Request,
    codes: list[str] = Form(...),
    names: list[str] = Form(...),
    lots: list[str] = Form(...),
    specs: list[str] = Form(...),
    size: str = Form(...),
    qty: int = Form(...),
):
    w, h = map(int, size.split("x"))
    items = [
        {"code": c, "name": n, "lot": l, "spec": s}
        for c, n, l, s in zip(codes, names, lots, specs)
    ]

    return templates.TemplateResponse(
        "label_item_excel_print.html",
        {
            "request": request,
            "items": items,
            "qty": qty,
            "width_mm": w,
            "height_mm": h,
        },
    )

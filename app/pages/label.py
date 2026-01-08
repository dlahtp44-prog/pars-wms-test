from fastapi import UploadFile, File
import pandas as pd
import io
@router.get("/로케이션/excel", response_class=HTMLResponse)
def label_location_excel_form(request: Request):
    return templates.TemplateResponse(
        "label_location_excel_form.html",
        {"request": request}
    )
@router.post("/로케이션/excel/preview", response_class=HTMLResponse)
async def label_location_excel_preview(
    request: Request,
    file: UploadFile = File(...),
    size: str = Form("70x40"),
    qty: int = Form(1),
):
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))

    # 컬럼명 정규화
    df.columns = [c.lower().strip() for c in df.columns]

    if "location" not in df.columns:
        return HTMLResponse("엑셀에 'location' 컬럼이 없습니다.", status_code=400)

    locations = (
        df["location"]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    return templates.TemplateResponse(
        "label_location_excel_preview.html",
        {
            "request": request,
            "locations": locations,
            "size": size,
            "qty": qty,
        },
    )
@router.post("/로케이션/excel/print", response_class=HTMLResponse)
def label_location_excel_print(
    request: Request,
    locations: list[str] = Form(...),
    size: str = Form(...),
    qty: int = Form(...),
):
    try:
        width_mm, height_mm = map(int, size.split("x"))
    except:
        width_mm, height_mm = 70, 40

    return templates.TemplateResponse(
        "label_location_excel_print.html",
        {
            "request": request,
            "locations": locations,
            "qty": qty,
            "width_mm": width_mm,
            "height_mm": height_mm,
        },
    )

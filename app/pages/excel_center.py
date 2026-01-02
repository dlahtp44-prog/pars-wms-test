from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/page", tags=["Excel Center"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/excel")
def excel_center(request: Request):
    return templates.TemplateResponse(
        "excel_center.html",
        {"request": request}
    )

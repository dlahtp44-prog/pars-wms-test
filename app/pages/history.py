from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/page", tags=["History Page"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/history")
def history_page(request: Request):
    return templates.TemplateResponse(
        "history.html",
        {"request": request}
    )

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/page/move", tags=["page-move"])

@router.get("", response_class=HTMLResponse)
def page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "move.html",
        {"request": request}
    )

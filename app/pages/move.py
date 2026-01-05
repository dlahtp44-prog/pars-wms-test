from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/page/move", tags=["page-move"])

@router.get("", response_class=HTMLResponse)
def page(request: Request):
    # main.py에서 설정한 templates 엔진을 그대로 사용
    return request.app.state.templates.TemplateResponse(
        "move.html",
        {"request": request}
    )

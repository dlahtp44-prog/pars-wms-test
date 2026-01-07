from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.core.auth import SESSION_COOKIE_NAME
from app.db import create_session, delete_session

router = APIRouter(tags=["page-auth"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

@router.post("/login")
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    token = create_session(username=username, password=password, hours=24)
    if not token:
        return templates.TemplateResponse("login.html", {"request": request, "error": "아이디/비밀번호가 올바르지 않습니다."}, status_code=401)

    resp = RedirectResponse(url="/", status_code=302)
    resp.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        max_age=60*60*24,
    )
    return resp

@router.get("/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME, "")
    delete_session(token)
    resp = RedirectResponse(url="/", status_code=302)
    resp.delete_cookie(SESSION_COOKIE_NAME)
    return resp

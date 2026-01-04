from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.paths import TEMPLATES_DIR
from app.db import get_db
from app.auth import verify_password

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter(tags=["auth"])

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/"):
    return templates.TemplateResponse("login.html", {"request": request, "next": next, "error": ""})

@router.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...), next: str = Form("/")):
    username = (username or "").strip()
    password = (password or "").strip()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, password_hash, role FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row or not verify_password(password, row["password_hash"]):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "next": next or "/", "error": "아이디 또는 비밀번호가 올바르지 않습니다."},
            status_code=401,
        )

    request.session["user"] = {"username": row["username"], "role": row["role"]}
    return RedirectResponse(url=(next or "/"), status_code=303)

@router.get("/logout")
def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/login", status_code=303)

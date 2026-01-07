from typing import Optional, Dict, Any
from fastapi import Request, HTTPException

from app.db import get_user_by_session

SESSION_COOKIE_NAME = "pars_session"

def current_user(request: Request) -> Optional[Dict[str, Any]]:
    token = request.cookies.get(SESSION_COOKIE_NAME, "")
    return get_user_by_session(token)

def require_admin(request: Request) -> Dict[str, Any]:
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    # v1.8: 간단 권한(현재 admin만)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
    return user

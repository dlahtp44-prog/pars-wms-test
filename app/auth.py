from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
from fastapi import Request
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@dataclass
class UserSession:
    username: str
    role: str = "user"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except Exception:
        return False

def get_user_session(request: Request) -> Optional[UserSession]:
    u = request.session.get("user") if hasattr(request, "session") else None
    if not u or not isinstance(u, dict):
        return None
    username = str(u.get("username", "")).strip()
    role = str(u.get("role", "user")).strip() or "user"
    if not username:
        return None
    return UserSession(username=username, role=role)

def require_login(request: Request) -> UserSession:
    user = get_user_session(request)
    if not user:
        # lazy import to avoid circular
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return user

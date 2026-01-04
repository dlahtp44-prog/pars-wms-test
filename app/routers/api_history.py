from fastapi import APIRouter
from app.db import query_history

router = APIRouter(prefix="/api/history", tags=["api-history"])

@router.get("")
def history(limit: int=200):
    return {"rows": query_history(limit=limit)}

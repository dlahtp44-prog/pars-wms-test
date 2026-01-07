from fastapi import APIRouter
router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("")
def history():
    return {"history": []}

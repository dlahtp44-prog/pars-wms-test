from fastapi import APIRouter
router = APIRouter(prefix="/api/move", tags=["move"])

@router.post("")
def move():
    return {"result": "move ok"}

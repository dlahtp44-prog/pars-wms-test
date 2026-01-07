from fastapi import APIRouter
router = APIRouter(prefix="/api/outbound", tags=["outbound"])

@router.post("")
def outbound():
    return {"result": "outbound ok"}

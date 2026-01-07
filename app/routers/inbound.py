from fastapi import APIRouter
router = APIRouter(prefix="/api/inbound", tags=["inbound"])

@router.post("")
def inbound():
    return {"result": "inbound ok"}

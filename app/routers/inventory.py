from fastapi import APIRouter
router = APIRouter(prefix="/api/inventory", tags=["inventory"])

@router.get("")
def inventory():
    return {"inventory": []}

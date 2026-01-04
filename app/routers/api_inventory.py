from fastapi import APIRouter
from app.db import query_inventory

router = APIRouter(prefix="/api/inventory", tags=["api-inventory"])

@router.get("")
def inventory(location: str="", item_code: str="", lot: str="", spec: str=""):
    return {"rows": query_inventory(location=location, item_code=item_code, lot=lot, spec=spec)}

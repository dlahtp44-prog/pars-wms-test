from fastapi import APIRouter
from app.db import query_inventory

router = APIRouter(prefix="/api/inventory", tags=["api-inventory"])

@router.get("")
def inventory(warehouse: str="", location: str="", brand: str="", item_code: str="", lot: str="", spec: str=""):
    return {"rows": query_inventory(warehouse=warehouse, location=location, brand=brand, item_code=item_code, lot=lot, spec=spec)}

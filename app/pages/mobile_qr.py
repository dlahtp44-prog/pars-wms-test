from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.utils.qr_format import parse_qr
templates=Jinja2Templates(directory=str(TEMPLATES_DIR))
router=APIRouter(prefix="/m/qr", tags=["mobile"])
@router.get("", response_class=HTMLResponse)
def qr_home(request:Request, mode:str=Query("inventory")):
    return templates.TemplateResponse("m/qr_scan.html",{"request":request,"mode":mode})
@router.post("/submit")
def submit(mode:str=Form("inventory"), qr_text:str=Form("")):
    data=parse_qr(qr_text)
    wh=data.get("warehouse","MAIN")
    loc=data.get("location","") or data.get("code","")
    if mode=="move":
        if not loc: return RedirectResponse("/m/qr?mode=move",302)
        return RedirectResponse(f"/m/move/select?warehouse={wh}&from_location={loc}",302)
    if not loc: return RedirectResponse("/m/qr?mode=inventory",302)
    return RedirectResponse(f"/m/qr/inventory?warehouse={wh}&location={loc}",302)

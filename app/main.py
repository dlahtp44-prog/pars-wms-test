from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db import init_db
from app.core.paths import STATIC_DIR
from app.routers import api_inbound, api_outbound, api_move, api_inventory, api_history, api_calendar, api_excel
from app.pages.index import router as index_router
from app.pages.inbound import router as inbound_page
from app.pages.outbound import router as outbound_page
from app.pages.move import router as move_page
from app.pages.inventory import router as inventory_page
from app.pages.history import router as history_page
from app.pages.calendar import router as calendar_page
from app.pages.excel import router as excel_page
from app.pages.mobile_home import router as mobile_home
from app.pages.mobile_qr import router as mobile_qr
from app.pages.mobile_inventory import router as mobile_inventory
from app.pages.mobile_move import router as mobile_move
app=FastAPI(title="PARS WMS", version="1.6")
init_db()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(index_router)
app.include_router(inbound_page); app.include_router(outbound_page); app.include_router(move_page)
app.include_router(inventory_page); app.include_router(history_page); app.include_router(calendar_page); app.include_router(excel_page)
app.include_router(mobile_home); app.include_router(mobile_qr); app.include_router(mobile_inventory); app.include_router(mobile_move)
app.include_router(api_inbound.router); app.include_router(api_outbound.router); app.include_router(api_move.router)
app.include_router(api_inventory.router); app.include_router(api_history.router); app.include_router(api_calendar.router); app.include_router(api_excel.router)

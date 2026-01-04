from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
import os
from fastapi.staticfiles import StaticFiles

from app.core.paths import STATIC_DIR
from app.db import init_db

# pages (PC)
from app.pages.login import router as login_router
from app.pages.calendar import router as calendar_page_router
from app.pages.index import router as index_router
from app.pages.inbound import router as inbound_page_router
from app.pages.outbound import router as outbound_page_router
from app.pages.move import router as move_page_router
from app.pages.inventory import router as inventory_page_router
from app.pages.history import router as history_page_router
from app.pages.excel_center import router as excel_center_page_router
from app.pages.excel_inbound import router as excel_inbound_page_router
from app.pages.excel_outbound import router as excel_outbound_page_router

# mobile pages
from app.pages.mobile_home import router as mobile_home_router
from app.pages.mobile_qr import router as mobile_qr_router
from app.pages.mobile_qr_inventory import router as mobile_qr_inventory_router
from app.pages.mobile_inventory_detail import router as mobile_inventory_detail_router
from app.pages.mobile_move import router as mobile_move_router

# api
from app.routers.api_calendar import router as api_calendar_router
from app.routers.api_inbound import router as api_inbound_router
from app.routers.api_outbound import router as api_outbound_router
from app.routers.api_move import router as api_move_router
from app.routers.api_inventory import router as api_inventory_router
from app.routers.api_history import router as api_history_router
from app.routers.excel_inbound import router as api_excel_inbound_router
from app.routers.excel_outbound import router as api_excel_outbound_router

app = FastAPI(title="PARS WMS", version="1.7.0-calendar")

# sessions (login)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "pars-wms-secret"),
    same_site="lax",
    https_only=bool(os.getenv("HTTPS_ONLY", "0") == "1"),
)


@app.on_event("startup")
def _startup():
    init_db()

# static
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# include routers (PC pages)
app.include_router(login_router)
app.include_router(calendar_page_router)
app.include_router(index_router)
app.include_router(inbound_page_router)
app.include_router(outbound_page_router)
app.include_router(move_page_router)
app.include_router(inventory_page_router)
app.include_router(history_page_router)
app.include_router(excel_center_page_router)
app.include_router(excel_inbound_page_router)
app.include_router(excel_outbound_page_router)

# include routers (mobile pages)
app.include_router(mobile_home_router)
app.include_router(mobile_qr_router)
app.include_router(mobile_qr_inventory_router)
app.include_router(mobile_inventory_detail_router)
app.include_router(mobile_move_router)

# include routers (api)
app.include_router(api_calendar_router)
app.include_router(api_inbound_router)
app.include_router(api_outbound_router)
app.include_router(api_move_router)
app.include_router(api_inventory_router)
app.include_router(api_history_router)
app.include_router(api_excel_inbound_router)
app.include_router(api_excel_outbound_router)

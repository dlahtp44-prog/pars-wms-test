import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import init_db

# =========================
# Pages (HTML)
# =========================
from app.pages.index import router as index_router
from app.pages.inbound import router as inbound_page_router
from app.pages.outbound import router as outbound_page_router
from app.pages.move import router as move_page_router
from app.pages.inventory import router as inventory_page_router
from app.pages.history import router as history_page_router
from app.pages.excel_outbound import router as excel_outbound_page_router

# Mobile pages
from app.pages.mobile_home import router as mobile_home_router
from app.pages.mobile_qr import router as mobile_qr_router
from app.pages.mobile_qr_inventory import router as mobile_qr_inventory_router
from app.pages.mobile_inventory_detail import router as mobile_inventory_detail_router

# =========================
# APIs
# =========================
from app.routers.api_inbound import router as api_inbound_router
from app.routers.api_outbound import router as api_outbound_router
from app.routers.api_move import router as api_move_router
from app.routers.api_inventory import router as api_inventory_router
from app.routers.api_history import router as api_history_router
from app.routers.excel_outbound import router as api_excel_outbound_router


# =========================
# App
# =========================
app = FastAPI(
    title="PARS WMS",
    version="1.6-stable"
)

# =========================
# Startup
# =========================
@app.on_event("startup")
def on_startup():
    init_db()


# =========================
# Base Dir
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# Static files
# =========================
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

# =========================
# Templates (🔥 핵심)
# =========================
templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)

# =========================
# Include Routers
# =========================

# PC pages
app.include_router(index_router)
app.include_router(inbound_page_router)
app.include_router(outbound_page_router)
app.include_router(move_page_router)
app.include_router(inventory_page_router)
app.include_router(history_page_router)
app.include_router(excel_outbound_page_router)

# Mobile pages
app.include_router(mobile_home_router)
app.include_router(mobile_qr_router)
app.include_router(mobile_qr_inventory_router)
app.include_router(mobile_inventory_detail_router)

# APIs
app.include_router(api_inbound_router)
app.include_router(api_outbound_router)
app.include_router(api_move_router)
app.include_router(api_inventory_router)
app.include_router(api_history_router)
app.include_router(api_excel_outbound_router)

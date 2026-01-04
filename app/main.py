from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.paths import STATIC_DIR
from app.db import init_db

# API routers
from app.routers import (
    api_inbound,
    api_outbound,
    api_move,
    api_inventory,
    api_history,
    api_excel_inbound,
    api_excel_outbound,
    api_calendar,
)

# Page routers (PC)
from app.pages import (
    index,
    inbound,
    outbound,
    move,
    inventory,
    history,
    excel_center,
    excel_inbound,
    excel_outbound,
    calendar,
)

# Mobile pages
from app.pages import (
    mobile_home,
    mobile_qr,
    mobile_qr_inventory,
    mobile_inventory_detail,
    mobile_move,
)

app = FastAPI(title="PARS WMS", version="1.7.0-calendar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# DB init
init_db()

# Include API routers
app.include_router(api_inbound.router)
app.include_router(api_outbound.router)
app.include_router(api_move.router)
app.include_router(api_inventory.router)
app.include_router(api_history.router)
app.include_router(api_excel_inbound.router)
app.include_router(api_excel_outbound.router)
app.include_router(api_calendar.router)

# Include page routers
app.include_router(index.router)
app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(move.router)
app.include_router(inventory.router)
app.include_router(history.router)
app.include_router(excel_center.router)
app.include_router(excel_inbound.router)
app.include_router(excel_outbound.router)
app.include_router(calendar.router)

# Mobile routers
app.include_router(mobile_home.router)
app.include_router(mobile_qr.router)
app.include_router(mobile_qr_inventory.router)
app.include_router(mobile_inventory_detail.router)
app.include_router(mobile_move.router)

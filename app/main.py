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
    excel_outbound,
    api_calendar,
)

# PC page routers
from app.pages import (
    index,
    inbound,
    outbound,
    move,
    inventory,
    history,
    excel_outbound as excel_outbound_page,
    calendar,
)

# Mobile page routers
from app.pages import (
    mobile_home,
    mobile_qr,
    mobile_qr_inventory,
    mobile_inventory_detail,
)

app = FastAPI(title="PARS WMS", version="base+calendar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# DB init
init_db()

# Include API routers
app.include_router(api_inbound.router)
app.include_router(api_outbound.router)
app.include_router(api_move.router)
app.include_router(api_inventory.router)
app.include_router(api_history.router)
app.include_router(excel_outbound.router)
app.include_router(api_calendar.router)

# Include PC page routers
app.include_router(index.router)
app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(move.router)
app.include_router(inventory.router)
app.include_router(history.router)
app.include_router(excel_outbound_page.router)
app.include_router(calendar.router)

# Include mobile page routers
app.include_router(mobile_home.router)
app.include_router(mobile_qr.router)
app.include_router(mobile_qr_inventory.router)
app.include_router(mobile_inventory_detail.router)

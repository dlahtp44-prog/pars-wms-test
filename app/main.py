from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.paths import STATIC_DIR
from app.db import init_db

# =========================
# API Routers
# =========================
from app.routers import (
    api_inbound,
    api_outbound,
    api_move,
    api_inventory,
    api_history,
    excel_inbound,
    excel_outbound,
    api_calendar,
)

# =========================
# PC Page Routers
# =========================
from app.pages import (
    index,
    inbound,
    outbound,
    move,
    inventory,
    history,
    excel_center,
    excel_inbound as page_excel_inbound,
    excel_outbound as page_excel_outbound,
    calendar,
)

# =========================
# Mobile Page Routers
# =========================
from app.pages import (
    mobile_home,
    mobile_qr,
    mobile_qr_inventory,
    mobile_inventory_detail,
)

# =========================
# Mobile Action Routers
# =========================
from app.routers import mobile_move


# =========================
# App Init
# =========================
app = FastAPI(
    title="PARS WMS",
    version="1.7.1-calendar-stable",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Static Files
# =========================
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# =========================
# DB Init
# =========================
init_db()

# =========================
# Include API Routers
# =========================
app.include_router(api_inbound.router)
app.include_router(api_outbound.router)
app.include_router(api_move.router)
app.include_router(api_inventory.router)
app.include_router(api_history.router)
app.include_router(excel_inbound.router)
app.include_router(excel_outbound.router)
app.include_router(api_calendar.router)

# =========================
# Include PC Page Routers
# =========================
app.include_router(index.router)
app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(move.router)
app.include_router(inventory.router)
app.include_router(history.router)
app.include_router(excel_center.router)
app.include_router(page_excel_inbound.router)
app.include_router(page_excel_outbound.router)
app.include_router(calendar.router)

# =========================
# Include Mobile Routers
# =========================
app.include_router(mobile_home.router)
app.include_router(mobile_qr.router)
app.include_router(mobile_qr_inventory.router)
app.include_router(mobile_inventory_detail.router)
app.include_router(mobile_move.router)

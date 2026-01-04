from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.paths import STATIC_DIR
from app.db import init_db

# =========================
# FastAPI App
# =========================
app = FastAPI(title="PARS WMS", version="1.7.x-stable")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Static
# =========================
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# =========================
# DB Init
# =========================
init_db()

# =========================
# API Routers
# =========================
from app.routers import (
    api_inbound,
    api_outbound,
    api_move,
    api_inventory,
    api_history,
    api_calendar,
    excel_inbound,
    excel_outbound,
)

app.include_router(api_inbound.router)
app.include_router(api_outbound.router)
app.include_router(api_move.router)
app.include_router(api_inventory.router)
app.include_router(api_history.router)
app.include_router(api_calendar.router)
app.include_router(excel_inbound.router)
app.include_router(excel_outbound.router)

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
# Mobile Routers
# =========================
from app.pages import (
    mobile_home,
    mobile_qr,
    mobile_qr_inventory,
    mobile_inventory_detail,
)

from app.routers import mobile_move

app.include_router(mobile_home.router)            # /m
app.include_router(mobile_qr.router)              # /m/qr
app.include_router(mobile_qr_inventory.router)    # /m/qr/inventory
app.include_router(mobile_inventory_detail.router)# /m/inventory/detail
app.include_router(mobile_move.router)            # /m/move

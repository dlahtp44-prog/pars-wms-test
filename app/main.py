from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .core.paths import STATIC_DIR

# API routers
from .routers import (
    api_inbound, api_outbound, api_move, api_inventory, api_history, api_calendar, api_excel
)

# Page routers
from .pages import (
    index, inbound, outbound, move, inventory, history, calendar, excel_center,
    mobile_home, mobile_qr, mobile_move
)

app = FastAPI(title="PARS WMS", version="1.6-final")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
def _startup():
    init_db()

# pages
app.include_router(index.router)
app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(move.router)
app.include_router(inventory.router)
app.include_router(history.router)
app.include_router(calendar.router)
app.include_router(excel_center.router)
app.include_router(mobile_home.router)
app.include_router(mobile_qr.router)
app.include_router(mobile_move.router)

# apis
app.include_router(api_inbound.router)
app.include_router(api_outbound.router)
app.include_router(api_move.router)
app.include_router(api_inventory.router)
app.include_router(api_history.router)
app.include_router(api_calendar.router)
app.include_router(api_excel.router)

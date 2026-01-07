from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import inbound, outbound, inventory, move, history

app = FastAPI(title="PARS WMS")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(inventory.router)
app.include_router(move.router)
app.include_router(history.router)

@app.get("/")
def root():
    return {"status": "PARS WMS OK"}


from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import inbound, outbound, move, inventory, history
from app.db.database import get_conn
from pathlib import Path

app = FastAPI(title="PARS WMS")

app.mount("/static", StaticFiles(directory="static"), name="static")

# init DB
schema = Path(__file__).parent / "db/schema.sql"
conn = get_conn()
conn.executescript(schema.read_text())
conn.commit()
conn.close()

app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(move.router)
app.include_router(inventory.router)
app.include_router(history.router)

@app.get("/")
def root():
    return {"status": "PARS WMS ALL-IN-ONE READY"}

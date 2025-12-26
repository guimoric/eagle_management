from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import crud, routes
from .db import SessionLocal, init_db

app = FastAPI(title="Eagle PM", version="0.1.0")

BASE_DIR = Path(__file__).parent
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(routes.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    with SessionLocal() as session:
        crud.update_release_statuses(session)
        session.commit()

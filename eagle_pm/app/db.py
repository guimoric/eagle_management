from __future__ import annotations

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_PATH = Path(os.getenv("EAGLE_PM_DB_PATH", "eagle_pm.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import crud, models  # ensure models are imported

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        crud.seed_index_tables(session)
        session.commit()


__all__ = ["Base", "engine", "SessionLocal", "get_session", "init_db"]

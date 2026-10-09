import datetime
from pathlib import Path
import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Register datetime adapters for Python 3.12+ / 3.14 sqlite3
sqlite3.register_adapter(datetime.datetime, lambda dt: dt.isoformat())
sqlite3.register_converter("DATETIME", lambda s: datetime.datetime.fromisoformat(s.decode("utf-8")))

DATABASE_URL = f"sqlite:///{(Path(__file__).resolve().parent.parent / 'retailcore.db').as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

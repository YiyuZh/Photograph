from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings


settings = get_settings()

engine = create_engine(
    settings.database_url_resolved,
    connect_args={"check_same_thread": False} if settings.database_url_resolved.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_runtime_schema() -> None:
    inspector = inspect(engine)
    if "results" in inspector.get_table_names():
        result_columns = {column["name"] for column in inspector.get_columns("results")}
        if "source_note" not in result_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE results ADD COLUMN source_note TEXT"))

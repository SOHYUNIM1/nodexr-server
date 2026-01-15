from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from app.core.config import settings

# =================================================
# SQLAlchemy Engine
# =================================================
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

# =================================================
# Session Factory (SessionLocal)
# =================================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# =================================================
# Base for ORM Models
# =================================================
Base = declarative_base()

# =================================================
# Dependency (FastAPI)
# =================================================
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
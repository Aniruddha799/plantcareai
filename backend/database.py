from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase  # DeclarativeBase is the modern SQLAlchemy 2.0 way

SQLALCHEMY_DATABASE_URL = "sqlite:///./plant_care.db"

# connect_args={"check_same_thread": False} is needed only for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models (SQLAlchemy 2.0+ style)."""
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.services.cloud_sql import get_engine


class Base(DeclarativeBase):
    pass


def get_session_factory():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db():
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

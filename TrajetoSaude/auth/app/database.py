from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


def _build_engine():
    if settings.cloud_sql_host:
        url = (
            f"postgresql+pg8000://{settings.cloud_sql_user}:{settings.cloud_sql_password}"
            f"@{settings.cloud_sql_host}:{settings.cloud_sql_port}/{settings.cloud_sql_database}"
        )
        return create_engine(url, pool_pre_ping=True)

    if not settings.cloud_sql_instance_connection_name:
        raise RuntimeError("Configure CLOUD_SQL_INSTANCE_CONNECTION_NAME ou CLOUD_SQL_HOST.")

    from google.cloud.sql.connector import Connector

    connector = Connector()

    def getconn():
        return connector.connect(
            settings.cloud_sql_instance_connection_name,
            "pg8000",
            user=settings.cloud_sql_user,
            password=settings.cloud_sql_password,
            db=settings.cloud_sql_database,
        )

    return create_engine("postgresql+pg8000://", creator=getconn, pool_pre_ping=True)


_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine

def _get_session_local():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


class Base(DeclarativeBase):
    pass


def get_db():
    db = _get_session_local()()
    try:
        yield db
    finally:
        db.close()

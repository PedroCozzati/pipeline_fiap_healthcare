from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import settings


def _build_engine() -> Engine:
     if settings.cloud_sql_host:
          url = (
               f"postgresql+pg8000://{settings.cloud_sql_user}:{settings.cloud_sql_password}"
               f"@{settings.cloud_sql_host}:{settings.cloud_sql_port}/{settings.cloud_sql_database}"
          )
          return create_engine(url, pool_pre_ping=True)

     if not settings.cloud_sql_instance_connection_name:
          raise RuntimeError(
               "Configure CLOUD_SQL_INSTANCE_CONNECTION_NAME ou CLOUD_SQL_HOST para usar o banco."
          )

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


_engine: Engine | None = None


def get_engine() -> Engine:
     global _engine
     if _engine is None:
          _engine = _build_engine()
     return _engine


@contextmanager
def get_connection():
     engine = get_engine()
     with engine.connect() as conn:
          yield conn


def execute_query(sql: str, params: dict | None = None) -> list[dict]:
     with get_connection() as conn:
          result = conn.execute(text(sql), params or {})
          if not result.returns_rows:
               conn.commit()
               return [{"rows_affected": result.rowcount}]
          return [dict(row._mapping) for row in result.fetchall()]

from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cloud_sql_instance_connection_name: str = ""
    cloud_sql_database: str = "traj-saude"
    cloud_sql_user: str = "traj-saude"
    cloud_sql_password: str = "traj-saude"
    cloud_sql_host: str | None = None
    cloud_sql_port: int = 5432

    jwt_secret_key: str = "changeme-please-set-in-env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24h

    infosimples_token: str = ""  # token da API infosimples para validação COREN


settings = Settings()


def setup_environment() -> None:
    creds = PROJECT_ROOT / "credentials" / "gcp-sa.json"
    if creds.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds.resolve())


setup_environment()

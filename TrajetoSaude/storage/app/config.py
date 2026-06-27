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

     gcp_project_id: str = "traj-saude"
     google_application_credentials: str = "credentials/gcp-sa.json"
     gcs_bucket_name: str = "traj-saude-us"
     gcs_artifacts_prefix: str = "model_evasao/v1/"

     cloud_sql_instance_connection_name: str = ""
     cloud_sql_database: str = "trajeto_saude"
     cloud_sql_user: str = "app_user"
     cloud_sql_password: str = ""

     cloud_sql_host: str | None = None
     cloud_sql_port: int = 5432


settings = Settings()


def setup_environment() -> None:
     creds = Path(settings.google_application_credentials)
     if not creds.is_absolute():
          creds = PROJECT_ROOT / settings.google_application_credentials
     if creds.exists():
          os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds.resolve())


setup_environment()

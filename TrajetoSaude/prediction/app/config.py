from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

# prediction/app/config.py → parents[1]=prediction, parents[2]=TrajetoSaude
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
     model_source: str = "gcs"
     model_local_path: str = "artefatos/risk_model.joblib"
     model_gcs_uri: str = "gs://traj-saude-us/model_evasao/v1/risk_model.joblib"
     gcp_reasoning_engine_url: str = ""
     storage_service_url: str = "http://localhost:8001"
     pipeline_base_dir: str = ""
     gcs_artifacts_prefix: str = "model_evasao/v1/"


settings = Settings()


def _resolve_from_root(path: str) -> Path:
     candidate = Path(path)
     if candidate.is_absolute():
          return candidate
     return PROJECT_ROOT / path


def resolve_pipeline_base_dir() -> Path:
     """Diretório base do pipeline dentro de TrajetoSaude (contém raw/ e output/)."""
     if settings.pipeline_base_dir.strip():
          return _resolve_from_root(settings.pipeline_base_dir)

     return (PROJECT_ROOT / "data").resolve()


def setup_environment() -> None:
     creds = _resolve_from_root(settings.google_application_credentials)
     if creds.exists():
          os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds.resolve())


def resolve_model_path() -> Path:
     raw = settings.model_local_path.strip()
     candidates: list[Path] = []

     if raw.startswith("gs://"):
          raise ValueError("MODEL_LOCAL_PATH deve ser caminho de arquivo, não URI gs://")

     configured = Path(raw)
     if configured.is_absolute():
          candidates.append(configured)
     else:
          candidates.extend([
               SERVICE_ROOT / raw,
               PROJECT_ROOT / "prediction" / raw,
               PROJECT_ROOT / raw,
          ])

     candidates.append(SERVICE_ROOT / "artefatos" / "risk_model.joblib")

     for path in candidates:
          if path.exists():
               return path.resolve()

     tried = ", ".join(str(p) for p in candidates)
     raise FileNotFoundError(f"Modelo local não encontrado. Caminhos testados: {tried}")


setup_environment()

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
     model_config = SettingsConfigDict(
          env_file=str(PROJECT_ROOT / ".env"),
          env_file_encoding="utf-8",
          extra="ignore",
     )

     gcp_project_id: str = ""
     google_application_credentials: str = "credentials/gcp-sa.json"

     # Reasoning Engine — paciente (chatbot de orientação)
     gcp_reasoning_engine_url: str = ""

     # Reasoning Engine — agente de saúde (suporte clínico à triagem)
     gcp_reasoning_engine_agente_url: str = ""

     model_path: str = "./artefatos/risk_model.joblib"


settings = Settings()


def resolve_reasoning_engine_url(agente: bool = False) -> str:
     if agente and settings.gcp_reasoning_engine_agente_url.strip():
          return settings.gcp_reasoning_engine_agente_url.strip()
     if settings.gcp_reasoning_engine_url.strip():
          return settings.gcp_reasoning_engine_url.strip()
     raise RuntimeError(
          "Configure GCP_REASONING_ENGINE_URL (e opcionalmente GCP_REASONING_ENGINE_AGENTE_URL) no .env."
     )

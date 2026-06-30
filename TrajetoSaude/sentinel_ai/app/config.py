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
     cors_origins: list[str] = ["http://localhost:4000", "http://localhost:4200"]
     gcp_reasoning_engine_url: str = (
        "https://us-west1-aiplatform.googleapis.com/v1/projects/traj-saude"
        "/locations/us-west1/reasoningEngines/4425112089333334016:streamQuery"
     )

     gcp_reasoning_engine_agente_url: str = (
        "https://us-west1-aiplatform.googleapis.com/v1/projects/traj-saude"
        "/locations/us-west1/reasoningEngines/4425112089333334016:streamQuery"
     )

     model_path: str = "./artefatos/risk_model.joblib"


settings = Settings()


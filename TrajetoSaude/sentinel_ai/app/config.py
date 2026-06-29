from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    cors_origins: list[str] = ["http://localhost:4000", "http://localhost:4200"]

    # Reasoning Engine — paciente (chatbot de orientação)
    gcp_reasoning_engine_url: str = (
        "https://us-west1-aiplatform.googleapis.com/v1/projects/traj-saude"
        "/locations/us-west1/reasoningEngines/4425112089333334016:query"
    )

    # Reasoning Engine — agente de saúde (suporte clínico à triagem)
    gcp_reasoning_engine_agente_url: str = (
        "https://us-west1-aiplatform.googleapis.com/v1/projects/traj-saude"
        "/locations/us-west1/reasoningEngines/4425112089333334016:query"
    )

    model_path: str = "./artefatos/risk_model.joblib"


settings = Settings()

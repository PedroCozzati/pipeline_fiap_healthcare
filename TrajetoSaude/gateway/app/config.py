from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
     model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

     cors_origins: list[str] = ["http://localhost:4200"]
     storage_service_url: str = "http://storage:8001"
     prediction_service_url: str = "http://prediction:8002"


settings = Settings()

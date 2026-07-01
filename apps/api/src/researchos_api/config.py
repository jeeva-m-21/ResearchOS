# mypy: disable-error-code="misc"
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/researchos"
    redis_url: str = "redis://localhost:6379/0"
    s3_bucket: str = "researchos-artifacts"
    deepseek_api_key: str = ""
    embedding_api_key: str = ""


settings = Settings()

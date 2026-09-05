from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MitraMetrology AI"
    environment: str = "dev"

    database_url: str = "postgresql+psycopg2://postgres@127.0.0.1:5432/mitrametrology"

    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 480
    jwt_issuer: str = "mitrametrology"

    storage_root: str = "backend/storage"

    max_image_mb: int = 20
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
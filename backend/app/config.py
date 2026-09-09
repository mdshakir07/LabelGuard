from functools import lru_cache
from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "LabelGuard"
    environment: str = "dev"

    database_url: str = "postgresql+psycopg2://postgres@127.0.0.1:5432/mitrametrology"

    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 480
    jwt_issuer: str = "labelguard"

    storage_root: str = "backend/storage"

    cors_origins: str = ""

    max_image_mb: int = 20
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp"]

    @property
    def resolved_storage_root(self) -> Path:
        """Absolute storage root, anchored to the repo, independent of CWD."""
        p = Path(self.storage_root)
        if not p.is_absolute():
            p = _REPO_ROOT / p
        return p.resolve()

    @property
    def cors_origin_list(self) -> list[str]:
        """Local defaults plus any origins configured via CORS_ORIGINS."""
        defaults = ["http://localhost:3000", "http://127.0.0.1:3000"]
        extra = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return list(dict.fromkeys(defaults + extra))


@lru_cache
def get_settings() -> Settings:
    return Settings()
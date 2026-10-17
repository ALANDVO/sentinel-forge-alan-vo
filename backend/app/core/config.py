"""Application settings."""
from __future__ import annotations

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_reload: bool = False
    database_url: str = "sqlite:///./sentinel_forge.db"
    demo_mode: bool = True
    api_key: str | None = None
    cors_origins: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_localhost(self) -> bool:
        return self.app_host in ("127.0.0.1", "localhost", "0.0.0.0") and not self.is_production

    @property
    def is_production(self) -> bool:
        return os_env("ENVIRONMENT", "development") == "production"

    def demo_mode_active(self) -> bool:
        return self.demo_mode and self.is_localhost


def os_env(name: str, default: str) -> str:
    return os.environ.get(name, default)


settings = Settings()
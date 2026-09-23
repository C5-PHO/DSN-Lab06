from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "SecureDocs"
    secret_key: str = os.getenv("SECUREDOCS_SECRET_KEY", "dev-only-change-me")
    database_url: str = os.getenv("SECUREDOCS_DATABASE_URL", "sqlite:///./secure_docs.db")
    access_token_minutes: int = int(os.getenv("SECUREDOCS_ACCESS_TOKEN_MINUTES", "60"))
    allow_context_headers: bool = _as_bool(
        os.getenv("SECUREDOCS_ALLOW_CONTEXT_HEADERS", "true")
    )


settings = Settings()


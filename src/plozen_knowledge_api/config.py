from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    postgres_db: str = "plozen_knowledge"
    postgres_user: str = "plozen"
    postgres_password: str | None = None
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 55432
    database_url: str | None = None
    api_host: str = "0.0.0.0"
    api_port: int = 8100
    embedding_provider: str = "fake"
    embedding_dimensions: int = 1536
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    knowledge_api_key: str | None = None
    allow_unauthenticated_dev: bool = False
    chunk_size: int = 850
    chunk_overlap: int = 120

    @property
    def psycopg_conninfo(self) -> str:
        if self.database_url:
            return self.database_url
        if not self.postgres_password:
            raise RuntimeError("POSTGRES_PASSWORD is required when DATABASE_URL is not set")
        return (
            f"dbname={self.postgres_db} "
            f"user={self.postgres_user} "
            f"password={self.postgres_password} "
            f"host={self.postgres_host} "
            f"port={self.postgres_port}"
        )


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        postgres_db=os.getenv("POSTGRES_DB", "plozen_knowledge"),
        postgres_user=os.getenv("POSTGRES_USER", "plozen"),
        postgres_password=os.getenv("POSTGRES_PASSWORD") or None,
        postgres_host=os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "127.0.0.1")),
        postgres_port=int(os.getenv("POSTGRES_PORT", "55432")),
        database_url=os.getenv("DATABASE_URL"),
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8100")),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "fake"),
        embedding_dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "1536")),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        knowledge_api_key=os.getenv("KNOWLEDGE_API_KEY"),
        allow_unauthenticated_dev=parse_bool(os.getenv("ALLOW_UNAUTHENTICATED_DEV"), default=False),
        chunk_size=int(os.getenv("CHUNK_SIZE", "850")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "120")),
    )

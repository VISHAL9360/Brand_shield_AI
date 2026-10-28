from functools import lru_cache
from typing import Any, Literal, Optional
import urllib.parse
from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(raw_url: str | None) -> tuple[str, dict[str, Any]]:
    """
    Smart Database URL Auto-Normalizer for BrandShield AI:
    - Normalizes postgres:// and postgresql:// -> postgresql+asyncpg://
    - Normalizes sqlite:// -> sqlite+aiosqlite://
    - Strips incompatible query parameters (sslmode, target_session_attrs) for asyncpg
    - Automatically maps cloud PostgreSQL providers (Neon, Supabase, Render, Tembo)
      or explicit sslmode=require to connect_args={"ssl": "require"}
    - Preserves unencrypted high-speed connections for local / docker PostgreSQL.
    """
    if not raw_url or not raw_url.strip():
        return "postgresql+asyncpg://postgres:postgres@localhost:5432/brandshield_ai", {}

    url = raw_url.strip()
    connect_args: dict[str, Any] = {}

    # Handle SQLite
    if "sqlite" in url:
        if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
            url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url, {"check_same_thread": False}

    # Normalize scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Parse URL components
    parsed = urllib.parse.urlsplit(url)
    hostname = (parsed.hostname or "").lower()
    query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)

    ssl_requested = False
    clean_params: list[tuple[str, str]] = []

    for k, v in query_params:
        k_lower = k.lower()
        if k_lower == "sslmode":
            if v.lower() in ("require", "verify-ca", "verify-full"):
                ssl_requested = True
        elif k_lower == "ssl":
            if v.lower() in ("true", "1", "require"):
                ssl_requested = True
        elif k_lower in ("target_session_attrs", "channel_binding"):
            continue
        else:
            clean_params.append((k, v))

    # Identify cloud postgres providers that mandate SSL
    cloud_domains = (
        "neon.tech", "supabase.co", "supabase.com", "render.com",
        "railway.app", "tembo.io", "cockroachlabs.cloud", "amazonaws.com",
    )
    is_cloud_host = any(domain in hostname for domain in cloud_domains)
    is_local_host = hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "docker", "postgres", "host.docker.internal")

    if ssl_requested or (is_cloud_host and not is_local_host):
        connect_args["ssl"] = "require"

    clean_query = urllib.parse.urlencode(clean_params)
    clean_url = urllib.parse.urlunsplit((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        clean_query,
        parsed.fragment,
    ))

    return clean_url, connect_args


class Settings(BaseSettings):
    """
    Production Application Configuration for BrandShield AI.
    Adheres to 12-factor application methodology and Pydantic v2 Settings.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    PROJECT_NAME: str = "BrandShield AI"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Security & JWT
    SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="Cryptographically secure secret key for JWT signing"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    HASH_CHAIN_SALT: str = Field(
        default="b5a8370d9e2948bb8f0b7305988147d3",
        description="Salt utilized for immutable Merkle audit hash chain calculation"
    )

    # Database & Pool Settings (PostgreSQL 16+ with pgvector)
    DATABASE_URL: str | None = Field(
        default=None,
        description="Full connection string (e.g. from Render or Heroku environment)"
    )
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "brandshield_ai"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: float = 30.0
    DB_POOL_RECYCLE: int = 1800  # 30 minutes
    DB_ECHO: bool = False

    @computed_field  # type: ignore[misc]
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        raw = self.DATABASE_URL or (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        url, _ = normalize_database_url(raw)
        return url

    @computed_field  # type: ignore[misc]
    @property
    def ASYNC_CONNECT_ARGS(self) -> dict[str, Any]:
        raw = self.DATABASE_URL or (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        _, args = normalize_database_url(raw)
        return args

    # CORS & Frontend Origins
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    CORS_ALLOW_ORIGIN_REGEX: str = r"^https://.*\.vercel\.app$"

    # Redis Cache & Token Bucket Rate Limiting
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL_SECONDS: int = 3600

    # RAG & Embeddings
    EMBEDDING_DIMENSION: int = 1536
    RRF_K_PARAMETER: int = 60
    VECTOR_SIMILARITY_THRESHOLD: float = 0.82

    # Privacy Gate & Safeguards
    STOCHASTIC_AUDIT_PROBABILITY: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Pseudo-random sampling fraction (5%) to inject shadow audits and combat human automation bias"
    )
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIME: int = 30  # seconds
    EXTERNAL_LLM_TIMEOUT_SECONDS: float = 0.5  # 500ms strict SLA watchdog
    OPENAI_API_KEY: Optional[str] = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns cached singleton application settings instance."""
    return Settings()

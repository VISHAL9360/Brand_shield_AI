import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
import logging
import random
from typing import Any, Awaitable, TypeVar

from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, StaticPool

from app.core.config import get_settings, normalize_database_url

logger = logging.getLogger("brandshield.infrastructure.db")
settings = get_settings()

T = TypeVar("T")

# ==============================================================================
# Asynchronous Database Engine Configuration
# ==============================================================================

def create_configured_async_engine(
    db_url: str | None = None,
    connect_args: dict[str, Any] | None = None,
) -> AsyncEngine:
    """Creates a resilient async engine tailored for PostgreSQL pooling or SQLite testing."""
    target_url = db_url or settings.ASYNC_DATABASE_URL
    clean_url, auto_args = normalize_database_url(target_url)

    merged_connect_args = dict(auto_args)
    if connect_args:
        merged_connect_args.update(connect_args)

    engine_kwargs: dict[str, Any] = {
        "echo": settings.DB_ECHO,
        "future": True,
    }
    if "sqlite" in clean_url:
        merged_connect_args.setdefault("check_same_thread", False)
        engine_kwargs["connect_args"] = merged_connect_args
        if ":memory:" in clean_url:
            engine_kwargs["poolclass"] = StaticPool
        else:
            engine_kwargs["poolclass"] = NullPool
    else:
        # High-concurrency enterprise PostgreSQL pooling
        engine_kwargs.update({
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
            "pool_pre_ping": True,
        })
        if merged_connect_args:
            engine_kwargs["connect_args"] = merged_connect_args

    return create_async_engine(clean_url, **engine_kwargs)


async_engine: AsyncEngine = create_configured_async_engine()

# ==============================================================================
# Async Session Factory
# ==============================================================================

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevents eager post-commit attribute eviction in async pipelines
    autoflush=False,         # Prevents unintended flushing during complex multi-step validations
)


# ==============================================================================
# Deadlock Retry & Explicit Transaction Boundaries
# ==============================================================================

def is_deadlock_exception(exc: Exception) -> bool:
    """
    Detects transient concurrency conflicts, PostgreSQL deadlocks, and SQLite lock contention:
    - Postgres SQLSTATE 40P01 (deadlock_detected)
    - Postgres SQLSTATE 40001 (serialization_failure)
    - SQLite 'database is locked' / 'database table is locked'
    """
    err_str = str(exc).lower()
    if isinstance(exc, (OperationalError, DBAPIError)):
        if "deadlock" in err_str or "locked" in err_str or "serialization" in err_str:
            return True
        orig = getattr(exc, "orig", None)
        if orig:
            orig_str = str(orig).lower()
            if "40p01" in orig_str or "40001" in orig_str or "locked" in orig_str or "deadlock" in orig_str:
                return True
    return "database is locked" in err_str or "deadlock detected" in err_str


async def execute_with_deadlock_retry(
    operation: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    initial_delay: float = 0.05,
    backoff_factor: float = 2.0,
) -> T:
    """
    Executes an async database operation with exponential backoff and randomized jitter
    when transient deadlocks or lock contention errors are detected.
    """
    attempt = 0
    delay = initial_delay
    while True:
        try:
            return await operation()
        except Exception as exc:
            attempt += 1
            if attempt > max_retries or not is_deadlock_exception(exc):
                raise
            jitter = random.uniform(0.5, 1.5)
            sleep_time = delay * jitter
            logger.warning(
                "Transient deadlock or lock contention detected (attempt %d/%d). Retrying in %.3fs: %s",
                attempt,
                max_retries,
                sleep_time,
                exc,
            )
            await asyncio.sleep(sleep_time)
            delay *= backoff_factor


@asynccontextmanager
async def atomic_transaction(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Explicit transaction boundary establishing a nested savepoint or atomic unit.
    Automatically commits on normal exit and rolls back cleanly on exception.
    """
    if session.in_nested_transaction():
        async with session.begin_nested():
            yield session
    else:
        async with session.begin():
            yield session


# ==============================================================================
# Dependency Injection Session Generator
# ==============================================================================

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency providing an isolated transactional asynchronous database session.
    Enforces atomic transaction boundaries with automatic deadlock retry semantics on commit.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session

            async def _commit_op():
                if session.is_active:
                    await session.commit()

            await execute_with_deadlock_retry(_commit_op, max_retries=3)
        except Exception as exc:
            if session.is_active:
                await session.rollback()
            logger.error(
                "Transaction aborted and rolled back due to unhandled exception: %s",
                exc,
                exc_info=True,
            )
            raise
        finally:
            await session.close()



# ==============================================================================
# Engine Lifecycle & Extension Management
# ==============================================================================

async def init_db_extensions(engine: AsyncEngine | None = None) -> bool:
    """
    Idempotently verifies and registers required PostgreSQL extensions
    ('uuid-ossp', 'pg_trgm', 'vector' for pgvector HNSW indexing) using savepoints.
    Gracefully falls back to PortableVector JSONB if pgvector C-extension is not installed.
    Returns True if pgvector is available, False otherwise.
    """
    target_engine = engine or async_engine
    if "sqlite" in str(target_engine.url):
        return False

    logger.info("Verifying PostgreSQL extensions (uuid-ossp, pg_trgm, vector)...")
    has_vector = True

    async with target_engine.connect() as conn:
        # 1. uuid-ossp
        try:
            async with conn.begin_nested():
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        except Exception as exc:
            logger.warning("Optional extension 'uuid-ossp' skipped or unavailable: %s", exc)

        # 2. pg_trgm
        try:
            async with conn.begin_nested():
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        except Exception as exc:
            logger.warning("Optional extension 'pg_trgm' skipped or unavailable: %s", exc)

        # 3. vector (pgvector)
        try:
            async with conn.begin_nested():
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            logger.info("Native pgvector extension verified and enabled successfully.")
            from app.infrastructure.db.custom_types import set_pgvector_available
            set_pgvector_available(True)
        except Exception as exc:
            logger.warning(
                "pgvector C-extension not available on target PostgreSQL instance: %s. "
                "Engaging PortableVector JSONB/ARRAY fallback mode.",
                exc,
            )
            from app.infrastructure.db.custom_types import set_pgvector_available
            set_pgvector_available(False)
            has_vector = False

        await conn.commit()

    return has_vector


async def init_db_tables(engine: AsyncEngine | None = None) -> None:
    """
    Idempotently creates and verifies all database tables and native enum types.
    Handles PortableVector fallback by detaching HNSW indexes when pgvector is absent.
    """
    target_engine = engine or async_engine
    is_postgres = "postgresql" in str(target_engine.url)

    logger.info("Verifying and creating database tables (engine=%s)...", target_engine.url.drivername)
    from app.infrastructure.db.base import Base
    import app.infrastructure.db.models  # noqa: F401 - registers models
    from app.domain.enums import (
        CreatorAction,
        DetectorSource,
        FindingCategory,
        GuidelineCategory,
        ReviewSignOff,
        SeverityLevel,
        TriageStatus,
        UserRole,
        WorkflowState,
    )
    from app.infrastructure.db.custom_types import is_pgvector_available

    enum_definitions = [
        ("user_role_enum", UserRole),
        ("workflow_state_enum", WorkflowState),
        ("guideline_category_enum", GuidelineCategory),
        ("finding_category_enum", FindingCategory),
        ("severity_level_enum", SeverityLevel),
        ("triage_status_enum", TriageStatus),
        ("detector_source_enum", DetectorSource),
        ("creator_action_enum", CreatorAction),
        ("review_signoff_enum", ReviewSignOff),
    ]

    async with target_engine.begin() as conn:
        if is_postgres:
            for type_name, enum_cls in enum_definitions:
                values = ", ".join(f"'{e.value}'" for e in enum_cls)
                await conn.execute(
                    text(f"""
                    DO $$ BEGIN
                        CREATE TYPE {type_name} AS ENUM ({values});
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                    """)
                )

        # If pgvector is unavailable on Postgres, temporarily detach HNSW indexes to avoid DDL failure
        vector_available = is_pgvector_available() if is_postgres else True
        detached_indexes = []
        if is_postgres and not vector_available:
            for table in Base.metadata.tables.values():
                for idx in list(table.indexes):
                    if getattr(idx, "dialect_options", {}).get("postgresql", {}).get("using") == "hnsw":
                        table.indexes.remove(idx)
                        detached_indexes.append((table, idx))

        try:
            await conn.run_sync(Base.metadata.create_all)
        finally:
            for table, idx in detached_indexes:
                table.indexes.add(idx)

    logger.info("Database tables verified/created successfully.")


async def init_db(engine: AsyncEngine | None = None) -> None:
    """
    Full database initialization sequence:
    1. Extensions registration
    2. Tables & schema creation
    3. Idempotent seed execution
    """
    target_engine = engine or async_engine
    await init_db_extensions(target_engine)
    await init_db_tables(target_engine)
    await init_db_seed()


async def init_db_seed() -> None:
    """
    Checks if database is unpopulated and executes idempotent seeding if empty.
    """
    from app.infrastructure.db.models import Workspace
    from app.infrastructure.db.seed import seed_database

    logger.info("Checking database seed status...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Workspace.id).limit(1))
        existing_workspace = result.scalar_one_or_none()

        if existing_workspace is None:
            logger.info("Database is empty. Executing idempotent seed script...")
            seed_result = await seed_database(session)
            logger.info("Idempotent database seeding complete: %s", seed_result)
        else:
            logger.info("Database already contains existing tenant workspace(s). Seeding skipped.")


async def check_db_health(session: AsyncSession) -> dict[str, Any]:
    """
    Executes a heartbeat query to validate database reachability, latency,
    and pgvector extension health for readiness/liveness probes.
    """
    try:
        result = await session.execute(text("SELECT 1 AS heartbeat, version() AS pg_version;"))
        row = result.mappings().one()
        return {
            "status": "healthy",
            "heartbeat": row["heartbeat"],
            "postgres_version": row["pg_version"],
        }
    except Exception as exc:
        logger.critical("Database health check failed: %s", exc)
        return {
            "status": "unhealthy",
            "error": str(exc),
        }


async def close_db_connection() -> None:
    """
    Gracefully disposes the database connection pool during application shutdown.
    """
    logger.info("Closing asynchronous database connection pool...")
    await async_engine.dispose()
    logger.info("Database connection pool disposed.")

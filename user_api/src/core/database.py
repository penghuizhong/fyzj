"""Database configuration and session management for SQLAlchemy ORM."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from core.config import settings


# Convert PostgreSQL connection string to async version
# postgresql:// -> postgresql+asyncpg://
def get_async_database_url() -> str:
    """Get async database URL for SQLAlchemy."""
    from core.config import settings
    from memory.postgres import get_postgres_connection_string

    sync_url = get_postgres_connection_string()
    # Replace postgresql:// with postgresql+asyncpg://
    return sync_url.replace("postgresql://", "postgresql+asyncpg://")


# Create async engine
async_engine = create_async_engine(
    get_async_database_url(),
    pool_size=settings.SQLALCHEMY_POOL_SIZE,
    max_overflow=settings.SQLALCHEMY_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.is_dev(),
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for declarative models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Get database session as async generator for FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

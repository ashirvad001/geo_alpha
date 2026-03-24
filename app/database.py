"""
Database connection management.
- PostgreSQL via SQLAlchemy async engine
- MongoDB via Motor async client
- Redis via redis-py async client
"""

from collections.abc import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# ═══════════════════════════════════════════════════════
# PostgreSQL (SQLAlchemy Async)
# ═══════════════════════════════════════════════════════

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async DB session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ═══════════════════════════════════════════════════════
# MongoDB (Motor)
# ═══════════════════════════════════════════════════════

_mongo_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Return the singleton Motor client."""
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.mongo_url)
    return _mongo_client


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Return the default MongoDB database."""
    return get_mongo_client()[settings.mongo_db_name]


async def close_mongo() -> None:
    """Close the Motor client (call at shutdown)."""
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None


# ═══════════════════════════════════════════════════════
# Redis
# ═══════════════════════════════════════════════════════

_redis_client: Redis | None = None


def get_redis() -> Redis:
    """Return the singleton Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis client (call at shutdown)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None

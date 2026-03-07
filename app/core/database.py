from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.settings import settings


def _normalize_database_url(raw_url: str) -> str:
	if raw_url.startswith("postgresql://") and "+asyncpg" not in raw_url:
		return raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
	return raw_url


DATABASE_URL = _normalize_database_url(settings.DATABASE_URL)
engine = create_async_engine(DATABASE_URL, pool_pre_ping = True)
SessionLocal = async_sessionmaker(bind = engine, class_ = AsyncSession, expire_on_commit = False)

Base = declarative_base()


async def get_db():
	async with SessionLocal() as db:
		yield db

from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


# Convert sqlite:// → sqlite+aiosqlite://
_url = settings.DATABASE_URL
if _url.startswith("sqlite://") and "+aiosqlite" not in _url:
    _url = _url.replace("sqlite://", "sqlite+aiosqlite://", 1)

engine = create_async_engine(_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def init_db():
    from app.db import models  # noqa: F401 — ensure models are registered
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

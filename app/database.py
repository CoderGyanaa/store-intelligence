"""
StoreMind — Database layer
SQLite (dev) / PostgreSQL (prod) via environment variable.
Uses aiosqlite for async SQLite support.
"""

import os
import json
import logging
from typing import Optional, AsyncGenerator

logger = logging.getLogger("storemind.db")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./storemind.db")
_IS_SQLITE = DATABASE_URL.startswith("sqlite")

# ---------------------------------------------------------------------------
# Async DB engine (SQLAlchemy 2.x style)
# ---------------------------------------------------------------------------
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime, Index
from sqlalchemy import select, func, and_, text
from datetime import datetime, timezone


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if _IS_SQLITE else {},
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    store_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    camera_id: Mapped[str] = mapped_column(String(64), nullable=False)
    visitor_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    timestamp: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    zone_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    dwell_ms: Mapped[int] = mapped_column(Integer, default=0)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    ingested_at: Mapped[str] = mapped_column(
        String(32),
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    __table_args__ = (
        Index("ix_store_ts", "store_id", "timestamp"),
        Index("ix_store_visitor", "store_id", "visitor_id"),
    )


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_status() -> dict:
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count()).select_from(EventRecord))
            count = result.scalar()
            return {"status": "ok", "event_count": count}
    except Exception as e:
        return {"status": "error", "error": str(e)}

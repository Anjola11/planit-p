"""Database initialization and session helpers.

This module creates the SQLAlchemy async engine and exposes helpers for
initializing the database schema and creating async sessions. The engine
is configured from `Config.DATABASE_URL` so it can be swapped between
environments (sqlite for local development, postgres for production,
etc.).
"""

from sqlalchemy.ext.asyncio import create_async_engine
from src.config import Config
from sqlmodel import SQLModel
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession


# Async engine used by the application. Set `echo=False` in production to
# avoid verbose SQL logging; `echo=True` can be helpful during development.
engine = create_async_engine(
    url=Config.DATABASE_URL,
    echo=True,
)


async def init_db():
    """Create database tables for all SQLModel models.

    This function should be called during application start-up (or from a
    migration task) to ensure required tables exist. Import model classes
    inside the function to avoid import-time side-effects and circular
    imports.
    """

    async with engine.begin() as conn:
        # Import models here to ensure they are registered with SQLModel's
        # metadata before `create_all` is invoked.
        from src.authentication.models import Vendors, Planners, SignupOtp, ResetPasswordOtp

        await conn.run_sync(SQLModel.metadata.create_all)


async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_Session():
    """Async context manager yielding a database session.

    Use this in dependency injection for request-scoped sessions, for
    example in FastAPI dependencies. The session is yielded inside an
    async context manager which ensures it is properly closed after use.
    """

    async with async_session_maker() as session:
        yield session
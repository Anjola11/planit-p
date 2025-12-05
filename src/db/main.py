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
    
    The function connects to the database and runs SQLModel.metadata.create_all
    to generate tables based on registered models. Existing tables are not
    modified or dropped.

    """
    async with engine.begin() as conn:
        # Import models here to ensure they are registered with SQLModel's
        # metadata before `create_all` is invoked.
        from src.authentication.models import Vendors, Planners, SignupOtp, ForgotPasswordOtp
        
        # Create all tables defined in imported models
        await conn.run_sync(SQLModel.metadata.create_all)

# Session factory configured for async operations
async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent lazy loading issues after commit
)

async def get_Session():
    #Async context manager yielding a database session.
    
   
    async with async_session_maker() as session:
        yield session
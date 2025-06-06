"""
Database connection and session management for the Realtime Voice Assistant.
Production-ready database handling with connection pooling and error recovery.
"""

import asyncio
import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import redis.asyncio as redis
from config import settings
from models import Base, User, VoiceSession, Memory, Task, SystemLog


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections, sessions, and operations."""
    
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        self.async_session_factory = None
        self.redis_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connections and create tables."""
        if self._initialized:
            return
        
        try:
            # Create synchronous engine
            self.engine = create_engine(
                settings.database.url,
                pool_size=settings.database.pool_size,
                max_overflow=settings.database.max_overflow,
                echo=settings.database.echo
            )
            
            # Create asynchronous engine
            async_url = settings.database.url.replace("postgresql://", "postgresql+asyncpg://")
            self.async_engine = create_async_engine(
                async_url,
                pool_size=settings.database.pool_size,
                max_overflow=settings.database.max_overflow,
                echo=settings.database.echo
            )
            
            # Create session factories
            self.session_factory = sessionmaker(
                bind=self.engine,
                class_=Session,
                expire_on_commit=False
            )
            
            self.async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Initialize Redis connection
            self.redis_client = redis.from_url(
                settings.redis.url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connections
            await self._test_connections()
            
            # Create tables
            await self._create_tables()
            
            self._initialized = True
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise
    
    async def _test_connections(self):
        """Test database and Redis connections."""
        try:
            # Test async database connection
            async with self.async_engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            # Test Redis connection
            await self.redis_client.ping()
            
            logger.info("All database connections tested successfully")
            
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables if they don't exist."""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database tables created/verified successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a synchronous database session with automatic cleanup."""
        if not self._initialized:
            raise RuntimeError("Database manager not initialized")
        
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an asynchronous database session with automatic cleanup."""
        if not self._initialized:
            raise RuntimeError("Database manager not initialized")
        
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Async database session error: {e}")
                raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((SQLAlchemyError, DisconnectionError))
    )
    async def execute_with_retry(self, operation, *args, **kwargs):
        """Execute database operation with automatic retry on failure."""
        try:
            async with self.get_async_session() as session:
                return await operation(session, *args, **kwargs)
        except Exception as e:
            logger.warning(f"Database operation failed, retrying: {e}")
            raise
    
    async def close(self):
        """Close all database connections."""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            if self.async_engine:
                await self.async_engine.dispose()
            
            if self.engine:
                self.engine.dispose()
            
            self._initialized = False
            logger.info("Database manager closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing database manager: {e}")


class MemoryRepository:
    """Repository for memory operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_memory(self, user_id: str, memory_type: str, key: str, 
                          content: dict, **kwargs) -> Memory:
        """Create a new memory entry."""
        async def _create(session: AsyncSession):
            memory = Memory(
                user_id=user_id,
                memory_type=memory_type,
                key=key,
                content=content,
                **kwargs
            )
            session.add(memory)
            await session.flush()
            await session.refresh(memory)
            return memory
        
        return await self.db_manager.execute_with_retry(_create)
    
    async def get_memory(self, user_id: str, key: str) -> Optional[Memory]:
        """Get memory by user ID and key."""
        async def _get(session: AsyncSession):
            from sqlalchemy import select
            stmt = select(Memory).where(Memory.user_id == user_id, Memory.key == key)
            result = await session.execute(stmt)
            memory = result.scalar_one_or_none()
            if memory:
                memory.access_count += 1
                from sqlalchemy.sql import func
                memory.last_accessed_at = func.now()
            return memory
        
        return await self.db_manager.execute_with_retry(_get)


class TaskRepository:
    """Repository for task operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_task(self, user_id: str, title: str, **kwargs) -> Task:
        """Create a new task."""
        async def _create(session: AsyncSession):
            task = Task(
                user_id=user_id,
                title=title,
                **kwargs
            )
            session.add(task)
            await session.flush()
            await session.refresh(task)
            return task
        
        return await self.db_manager.execute_with_retry(_create)


class SessionRepository:
    """Repository for voice session operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_session(self, user_id: str, **kwargs) -> VoiceSession:
        """Create a new voice session."""
        async def _create(session: AsyncSession):
            voice_session = VoiceSession(
                user_id=user_id,
                **kwargs
            )
            session.add(voice_session)
            await session.flush()
            await session.refresh(voice_session)
            return voice_session
        
        return await self.db_manager.execute_with_retry(_create)


# Global database manager instance
db_manager = DatabaseManager()

# Repository instances
memory_repo = MemoryRepository(db_manager)
task_repo = TaskRepository(db_manager)
session_repo = SessionRepository(db_manager)


async def initialize_database():
    """Initialize the database manager."""
    await db_manager.initialize()


async def cleanup_database():
    """Cleanup database connections."""
    await db_manager.close()


# Database health check functions
async def check_database_health() -> dict:
    """Check database health status."""
    health = {
        "database": False,
        "redis": False,
        "error": None
    }
    
    try:
        # Check database
        async with db_manager.get_async_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        health["database"] = True
        
        # Check Redis
        await db_manager.redis_client.ping()
        health["redis"] = True
        
    except Exception as e:
        health["error"] = str(e)
        logger.error(f"Database health check failed: {e}")
    
    return health

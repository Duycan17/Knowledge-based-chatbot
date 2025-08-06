import asyncpg
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):
        self.pool = None
        self.database_url = settings.neon_database_url
        
        # Connection pool configuration from settings
        self.min_size = settings.db_min_connections
        self.max_size = settings.db_max_connections

    async def connect(self):
        """Tạo connection pool với optimized settings"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.min_size,
                max_size=self.max_size
            )
            logger.info("Connected to Neon PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Đóng connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from database")

    async def get_pool(self):
        """Lấy connection pool"""
        if not self.pool:
            await self.connect()
        return self.pool

    async def get_connection(self):
        """Lấy connection từ pool"""
        if not self.pool:
            await self.connect()
        return await self.pool.acquire()

    async def release_connection(self, conn):
        """Release connection về pool"""
        if self.pool:
            await self.pool.release(conn) 
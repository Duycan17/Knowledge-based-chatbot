import asyncpg
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        from config.settings import settings
        self.database_url = settings.neon_database_url
        
    async def connect(self):
        """Tạo connection pool với Neon PostgreSQL"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
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
        return self.pool 
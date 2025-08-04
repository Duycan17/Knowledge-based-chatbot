import logging

logger = logging.getLogger(__name__)


class DatabaseSchema:
    @staticmethod
    async def create_tables(pool):
        """Tạo tables nếu chưa tồn tại"""
        async with pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Create documents table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    filename TEXT NOT NULL,
                    content TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    embedding vector(768),
                    metadata JSONB DEFAULT '{}',
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create audit_logs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    chat_id UUID PRIMARY KEY,
                    question TEXT NOT NULL,
                    response TEXT NOT NULL,
                    retrieved_docs JSONB DEFAULT '[]',
                    latency_ms INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    feedback TEXT,
                    model_confidence FLOAT
                )
            """)
            
            # Create index for similarity search
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                ON documents USING hnsw (embedding vector_cosine_ops)
            """)
            
            logger.info("Database tables created successfully") 
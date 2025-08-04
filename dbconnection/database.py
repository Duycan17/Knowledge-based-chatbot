import logging
from .connection import DatabaseConnection
from .schema import DatabaseSchema
from .document_repository import DocumentRepository
from .audit_repository import AuditRepository

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.connection = DatabaseConnection()
        self.document_repo = None
        self.audit_repo = None

    async def connect(self):
        """Tạo connection pool và khởi tạo repositories"""
        await self.connection.connect()
        pool = await self.connection.get_pool()
        
        # Create tables
        await DatabaseSchema.create_tables(pool)
        
        # Initialize repositories
        self.document_repo = DocumentRepository(pool)
        self.audit_repo = AuditRepository(pool)
        
        logger.info("Database manager initialized successfully")

    async def disconnect(self):
        """Đóng connection pool"""
        await self.connection.disconnect()

    # Document operations
    async def insert_document(self, document):
        return await self.document_repo.insert_document(document)

    async def get_document(self, doc_id):
        return await self.document_repo.get_document(doc_id)

    async def get_all_documents(self, page=1, size=10):
        return await self.document_repo.get_all_documents(page, size)

    async def update_document(self, doc_id, content=None, metadata=None):
        return await self.document_repo.update_document(doc_id, content, metadata)

    async def update_document_status(self, doc_id, status):
        return await self.document_repo.update_document_status(doc_id, status)

    async def delete_document(self, doc_id):
        return await self.document_repo.delete_document(doc_id)

    async def search_similar_documents(self, embedding, limit=5):
        return await self.document_repo.search_similar_documents(embedding, limit)

    async def get_document_chunks(self, doc_id):
        return await self.document_repo.get_document_chunks(doc_id)

    # Audit operations
    async def insert_audit_log(self, audit_log):
        return await self.audit_repo.insert_audit_log(audit_log)

    async def get_audit_log(self, chat_id):
        return await self.audit_repo.get_audit_log(chat_id)


# Global database manager instance
db_manager = DatabaseManager() 
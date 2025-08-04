import os
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from datetime import datetime

from model.models import Document, AuditLog
from dbconnection.database import db_manager
from .file_processor import FileProcessingService
from .ai_service import AIService

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self):
        self.file_processor = FileProcessingService()
        self.ai_service = AIService()

    async def upload_file(self, file_path: str, filename: str, file_size: int) -> Document:
        """Upload và process file"""
        is_valid, message = await self.file_processor.validate_file(filename, file_size)
        if not is_valid:
            raise ValueError(message)
        
        document = await self.file_processor.process_file(file_path, filename, file_size)
        return document

    async def get_documents(self, page: int = 1, size: int = 10) -> tuple[List[Document], int]:
        """Lấy danh sách documents"""
        return await db_manager.get_all_documents(page, size)

    async def get_document(self, doc_id: UUID) -> Optional[Document]:
        """Lấy document theo ID"""
        return await db_manager.get_document(doc_id)

    async def update_document(self, doc_id: UUID, content: str = None, metadata: Dict = None) -> bool:
        """Cập nhật document"""
        return await db_manager.update_document(doc_id, content, metadata)

    async def delete_document(self, doc_id: UUID) -> bool:
        """Xóa document và file trong file system"""
        # Get document info first
        document = await self.get_document(doc_id)
        if not document:
            return False
        
        # Delete from database (including chunks)
        success = await db_manager.delete_document(doc_id)
        
        if success:
            # Delete file from file system
            from utils.file_utils import delete_file_safely
            file_path = document.metadata.get("file_path")
            if file_path:
                delete_file_safely(file_path)
            else:
                logger.warning(f"No file_path found in metadata for document {doc_id}")
        
        return success

    async def delete_multiple_documents(self, doc_ids: List[UUID]) -> Dict[str, Any]:
        """Xóa nhiều documents cùng lúc"""
        results = {
            "successful": [],
            "failed": [],
            "total_requested": len(doc_ids),
            "total_successful": 0,
            "total_failed": 0
        }
        
        for doc_id in doc_ids:
            try:
                success = await self.delete_document(doc_id)
                if success:
                    results["successful"].append(str(doc_id))
                    results["total_successful"] += 1
                else:
                    results["failed"].append(str(doc_id))
                    results["total_failed"] += 1
            except Exception as e:
                logger.error(f"Error deleting document {doc_id}: {e}")
                results["failed"].append(str(doc_id))
                results["total_failed"] += 1
        
        return results

    async def chat(self, question: str) -> tuple[str, List[Document], int, UUID]:
        """Chat với knowledge base"""
        import time
        from uuid import uuid4
        
        start_time = time.time()
        
        # Search relevant documents
        relevant_docs = await self.ai_service.search_relevant_documents(question)
        
        # Generate response
        response = await self.ai_service.generate_response(question, relevant_docs)
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Generate chat ID
        chat_id = uuid4()
        
        # Create audit log
        audit_log = AuditLog(
            chat_id=chat_id,
            question=question,
            response=response,
            retrieved_docs=[{"id": str(doc.id), "filename": doc.filename} for doc in relevant_docs],
            latency_ms=latency_ms
        )
        
        # Save audit log
        await db_manager.insert_audit_log(audit_log)
        
        return response, relevant_docs, latency_ms, chat_id

    async def get_document_chunks(self, doc_id: UUID) -> List[Document]:
        """Lấy chunks của document"""
        return await db_manager.get_document_chunks(doc_id)

    async def get_audit_log(self, chat_id: UUID) -> Optional[AuditLog]:
        """Lấy audit log theo chat_id"""
        return await db_manager.get_audit_log(chat_id) 
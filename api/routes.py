import os
import logging
from datetime import datetime
from typing import List
from uuid import UUID
from fastapi import HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse

from model.models import (
    DocumentResponse, DocumentListResponse, ChatRequest, ChatResponse,
    AuditLogResponse, UploadResponse, ErrorResponse, BatchDeleteResponse, BatchUploadResponse
)
from service.knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)


class APIRoutes:
    def __init__(self, knowledge_base_service: KnowledgeBaseService):
        self.knowledge_base_service = knowledge_base_service

    async def upload_file(self, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
        """
        Upload file text và process thành embeddings
        
        - **file**: File text (.txt, .md, .csv, .json) để upload
        - **max_size**: 10MB
        """
        try:
            # Validate file
            if not file.filename:
                raise HTTPException(status_code=400, detail="No file provided")
            
            # Get file size
            file_size = 0
            content = await file.read()
            file_size = len(content)
            
            from config.settings import settings
            from utils.file_utils import create_upload_directory, generate_safe_filename, get_file_path
            
            # Create file in uploads directory
            create_upload_directory(settings.upload_dir)
            
            # Generate unique filename
            safe_filename = generate_safe_filename(file.filename)
            file_path = get_file_path(settings.upload_dir, safe_filename)
            
            # Write file
            with open(file_path, "wb") as f:
                f.write(content)
            
            try:
                # Process file
                document = await self.knowledge_base_service.upload_file(
                    file_path, file.filename, file_size
                )
                
                return UploadResponse(
                    file_id=document.id,
                    filename=document.filename,
                    status=document.status,
                    message="File uploaded successfully and processing started",
                    file_size=document.file_size
                )
                
            finally:
                pass
                # Clean up temporary file (optional - comment out to keep files)
                # if os.path.exists(temp_file_path):
                #     os.unlink(temp_file_path)
                    
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def upload_multiple_files(self, background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
        """
        Upload nhiều file text và process thành embeddings
        
        - **files**: List các file text (.txt, .md, .csv, .json) để upload
        - **max_size**: 10MB per file
        - **max_files**: 50 files per request
        """
        try:
            # Validate input
            if not files:
                raise HTTPException(status_code=400, detail="No files provided")
            
            # Limit number of files
            if len(files) > 50:
                raise HTTPException(status_code=400, detail="Too many files. Maximum 50 files allowed per request.")
            
            uploads = []
            errors = []
            successful_count = 0
            failed_count = 0
            
            from config.settings import settings
            from utils.file_utils import create_upload_directory, generate_safe_filename, get_file_path
            
            # Create upload directory
            create_upload_directory(settings.upload_dir)
            
            for file in files:
                try:
                    # Validate file
                    if not file.filename:
                        errors.append({
                            "filename": "unknown",
                            "error": "No filename provided"
                        })
                        failed_count += 1
                        continue
                    
                    # Get file size
                    file_size = 0
                    content = await file.read()
                    file_size = len(content)
                    
                    # Validate file using FileProcessingService
                    from service.file_processor import FileProcessingService
                    file_processor = FileProcessingService()
                    is_valid, validation_message = await file_processor.validate_file(file.filename, file_size)
                    
                    if not is_valid:
                        errors.append({
                            "filename": file.filename,
                            "error": validation_message
                        })
                        failed_count += 1
                        continue
                    
                    # Generate unique filename
                    safe_filename = generate_safe_filename(file.filename)
                    file_path = get_file_path(settings.upload_dir, safe_filename)
                    
                    # Write file
                    with open(file_path, "wb") as f:
                        f.write(content)
                    
                    try:
                        # Process file
                        document = await self.knowledge_base_service.upload_file(
                            file_path, file.filename, file_size
                        )
                        
                        upload_response = UploadResponse(
                            file_id=document.id,
                            filename=document.filename,
                            status=document.status,
                            message="File uploaded successfully and processing started",
                            file_size=document.file_size
                        )
                        
                        uploads.append(upload_response)
                        successful_count += 1
                        
                    except Exception as e:
                        errors.append({
                            "filename": file.filename,
                            "error": str(e)
                        })
                        failed_count += 1
                        
                except Exception as e:
                    errors.append({
                        "filename": file.filename if file.filename else "unknown",
                        "error": str(e)
                    })
                    failed_count += 1
            
            return BatchUploadResponse(
                message=f"Batch upload completed. {successful_count} successful, {failed_count} failed",
                total_files=len(files),
                successful_uploads=successful_count,
                failed_uploads=failed_count,
                uploads=uploads,
                errors=errors
            )
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in batch upload: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_documents(self, page: int = 1, size: int = 10):
        """
        Lấy danh sách documents với pagination
        
        - **page**: Page number (default: 1)
        - **size**: Page size (default: 10)
        """
        try:
            documents, total = await self.knowledge_base_service.get_documents(page, size)
            
            return DocumentListResponse(
                documents=[
                    DocumentResponse(
                        id=doc.id,
                        filename=doc.filename,
                        content=doc.content,
                        file_size=doc.file_size,
                        metadata=doc.metadata,
                        created_at=doc.created_at,
                        updated_at=doc.updated_at,
                        status=doc.status
                    )
                    for doc in documents
                ],
                total=total,
                page=page,
                size=size
            )
            
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_document(self, doc_id: UUID):
        """
        Lấy document theo ID
        
        - **doc_id**: Document ID
        """
        try:
            document = await self.knowledge_base_service.get_document(doc_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            return DocumentResponse(
                id=document.id,
                filename=document.filename,
                content=document.content,
                file_size=document.file_size,
                metadata=document.metadata,
                created_at=document.created_at,
                updated_at=document.updated_at,
                status=document.status
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_document_chunks(self, doc_id: UUID):
        """
        Lấy chunks của document
        
        - **doc_id**: Document ID
        """
        try:
            chunks = await self.knowledge_base_service.get_document_chunks(doc_id)
            
            return {
                "document_id": str(doc_id),
                "chunks": [
                    {
                        "id": str(chunk.id),
                        "filename": chunk.filename,
                        "content": chunk.content,
                        "metadata": chunk.metadata,
                        "status": chunk.status.value
                    }
                    for chunk in chunks
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting document chunks {doc_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def update_document(self, doc_id: UUID, content: str = None, metadata: dict = None):
        """
        Cập nhật document
        
        - **doc_id**: Document ID
        - **content**: New content (optional)
        - **metadata**: New metadata (optional)
        """
        try:
            success = await self.knowledge_base_service.update_document(doc_id, content, metadata)
            if not success:
                raise HTTPException(status_code=404, detail="Document not found")
            
            return {"message": "Document updated successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def delete_document(self, doc_id: UUID):
        """
        Xóa document theo ID
        
        - **doc_id**: Document ID
        """
        try:
            success = await self.knowledge_base_service.delete_document(doc_id)
            if not success:
                raise HTTPException(status_code=404, detail="Document not found")
            
            return {"message": "Document deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def delete_multiple_documents(self, doc_ids: List[UUID]):
        """
        Xóa nhiều documents cùng lúc
        
        - **doc_ids**: List of Document IDs
        """
        try:
            if not doc_ids:
                raise HTTPException(status_code=400, detail="No document IDs provided")
            
            # Validate input - limit to reasonable number
            if len(doc_ids) > 100:
                raise HTTPException(status_code=400, detail="Too many documents requested. Maximum 100 documents allowed.")
            
            # Remove duplicates
            unique_doc_ids = list(set(doc_ids))
            if len(unique_doc_ids) != len(doc_ids):
                logger.info(f"Removed {len(doc_ids) - len(unique_doc_ids)} duplicate document IDs")
            
            results = await self.knowledge_base_service.delete_multiple_documents(unique_doc_ids)
            
            return BatchDeleteResponse(
                message=f"Batch delete completed. {results['total_successful']} successful, {results['total_failed']} failed",
                results=results
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in batch delete: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def retry_document_processing(self, doc_id: UUID):
        """
        Retry processing document nếu bị lỗi
        
        - **doc_id**: Document ID
        """
        try:
            document = await self.knowledge_base_service.get_document(doc_id)
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Retry processing
            await self.knowledge_base_service.file_processor._process_document_async(document)
            
            return {"message": "Document processing retry started"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrying document processing {doc_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def chat(self, request: ChatRequest):
        """
        Chat với knowledge base
        
        - **question**: User question
        """
        try:
            response, retrieved_docs, latency_ms, chat_id = await self.knowledge_base_service.chat(
                request.question
            )
            
            return ChatResponse(
                chat_id=chat_id,
                response=response,
                retrieved_docs=[{"id": str(doc.id), "filename": doc.filename} for doc in retrieved_docs]
            )
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_audit_log(self, chat_id: UUID):
        """
        Lấy audit log cho chat session
        
        - **chat_id**: Chat ID
        """
        try:
            audit_log = await self.knowledge_base_service.get_audit_log(chat_id)
            if not audit_log:
                raise HTTPException(status_code=404, detail="Audit log not found")
            
            return AuditLogResponse(
                chat_id=audit_log.chat_id,
                question=audit_log.question,
                response=audit_log.response,
                retrieved_docs=audit_log.retrieved_docs,
                latency_ms=audit_log.latency_ms,
                timestamp=audit_log.timestamp,
                feedback=audit_log.feedback,
                model_confidence=audit_log.model_confidence
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting audit log {chat_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") 
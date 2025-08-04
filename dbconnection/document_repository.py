import json
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from model.models import Document, FileStatus

logger = logging.getLogger(__name__)


class DocumentRepository:
    def __init__(self, pool):
        self.pool = pool

    async def insert_document(self, document: Document) -> UUID:
        """Thêm document mới vào database"""
        async with self.pool.acquire() as conn:
            # Handle embedding properly for pgvector
            embedding_param = None
            if document.embedding:
                embedding_param = f"[{','.join(map(str, document.embedding))}]"
            
            query = """
                INSERT INTO documents (id, filename, content, file_size, embedding, metadata, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """
            result = await conn.fetchval(
                query,
                document.id,
                document.filename,
                document.content,
                document.file_size,
                embedding_param,
                json.dumps(document.metadata),
                document.status.value
            )
            return result

    async def get_document(self, doc_id: UUID) -> Optional[Document]:
        """Lấy document theo ID"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT id, filename, content, file_size, embedding, metadata, status, created_at, updated_at
                FROM documents WHERE id = $1
            """
            row = await conn.fetchrow(query, doc_id)
            if row:
                return Document(
                    id=row['id'],
                    filename=row['filename'],
                    content=row['content'],
                    file_size=row['file_size'],
                    embedding=row['embedding'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    status=FileStatus(row['status'])
                )
            return None

    async def get_all_documents(self, page: int = 1, size: int = 10) -> tuple[List[Document], int]:
        """Lấy danh sách original documents với pagination"""
        async with self.pool.acquire() as conn:
            # Get total count of original documents (not chunks)
            count_query = """
                SELECT COUNT(*) FROM documents 
                WHERE filename NOT LIKE '%_chunk_%'
            """
            total = await conn.fetchval(count_query)
            
            # Get documents with pagination
            offset = (page - 1) * size
            query = """
                SELECT id, filename, content, file_size, embedding, metadata, status, created_at, updated_at
                FROM documents 
                WHERE filename NOT LIKE '%_chunk_%'
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """
            rows = await conn.fetch(query, size, offset)
            
            documents = []
            for row in rows:
                doc = Document(
                    id=row['id'],
                    filename=row['filename'],
                    content=row['content'],
                    file_size=row['file_size'],
                    embedding=row['embedding'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    status=FileStatus(row['status'])
                )
                documents.append(doc)
            
            return documents, total

    async def update_document(self, doc_id: UUID, content: str = None, metadata: Dict = None) -> bool:
        """Cập nhật document"""
        async with self.pool.acquire() as conn:
            updates = []
            values = [doc_id]
            param_count = 1
            
            if content is not None:
                updates.append(f"content = ${param_count + 1}")
                values.append(content)
                param_count += 1
            
            if metadata is not None:
                updates.append(f"metadata = ${param_count + 1}")
                values.append(json.dumps(metadata))
                param_count += 1
            
            if not updates:
                return False
            
            updates.append("updated_at = NOW()")
            query = f"UPDATE documents SET {', '.join(updates)} WHERE id = $1"
            
            result = await conn.execute(query, *values)
            return result.split()[-1] != "0"

    async def update_document_status(self, doc_id: UUID, status: FileStatus) -> bool:
        """Cập nhật status của document"""
        async with self.pool.acquire() as conn:
            query = "UPDATE documents SET status = $2, updated_at = NOW() WHERE id = $1"
            result = await conn.execute(query, doc_id, status.value)
            return result.split()[-1] != "0"

    async def delete_document(self, doc_id: UUID) -> bool:
        """Xóa document theo ID và tất cả chunks của nó"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # First, get the document to find file path
                doc_query = "SELECT filename, metadata FROM documents WHERE id = $1"
                doc_row = await conn.fetchrow(doc_query, doc_id)
                
                if not doc_row:
                    logger.warning(f"Document {doc_id} not found for deletion")
                    return False
                
                # Delete all chunks of this document
                chunks_query = """
                    DELETE FROM documents 
                    WHERE filename LIKE $1 AND metadata->>'parent_document_id' = $2
                """
                pattern = f"%_chunk_%"
                chunks_result = await conn.execute(chunks_query, pattern, str(doc_id))
                chunks_deleted = int(chunks_result.split()[-1])
                logger.info(f"Deleted {chunks_deleted} chunks for document {doc_id}")
                
                # Delete the original document
                query = "DELETE FROM documents WHERE id = $1"
                result = await conn.execute(query, doc_id)
                doc_deleted = result.split()[-1] != "0"
                
                if doc_deleted:
                    logger.info(f"Successfully deleted document {doc_id} and {chunks_deleted} chunks")
                else:
                    logger.error(f"Failed to delete document {doc_id}")
                
                return doc_deleted

    async def search_similar_documents(self, embedding: List[float], limit: int = 5) -> List[Document]:
        """Tìm documents tương tự dựa trên vector similarity - chỉ select trường cần thiết"""
        async with self.pool.acquire() as conn:
            # Format embedding for pgvector
            embedding_param = f"[{','.join(map(str, embedding))}]"
            
            # Vector search với pgvector - chỉ select trường cần thiết
            query = """
                SELECT id, filename, content, metadata, status,
                       embedding <=> $1 as similarity_score
                FROM documents 
                WHERE embedding IS NOT NULL AND status = 'completed'
                ORDER BY embedding <=> $1
                LIMIT $2
            """
            rows = await conn.fetch(query, embedding_param, limit)
            
            documents = []
            for row in rows:
                # Parse metadata và thêm similarity score
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                metadata['similarity_score'] = float(row['similarity_score'])
                
                doc = Document(
                    id=row['id'],
                    filename=row['filename'],
                    content=row['content'],
                    file_size=0,  # Không cần thiết cho search
                    embedding=None,  # Không cần thiết cho search result
                    metadata=metadata,
                    created_at=None,  # Không cần thiết cho search
                    updated_at=None,  # Không cần thiết cho search
                    status=FileStatus(row['status'])
                )
                documents.append(doc)
            
            return documents

    async def get_document_chunks(self, doc_id: UUID) -> List[Document]:
        """Lấy chunks của document - chỉ select trường cần thiết"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT id, filename, content, metadata, status
                FROM documents 
                WHERE filename LIKE $1 AND metadata->>'parent_document_id' = $2
                ORDER BY (metadata->>'chunk_index')::int
            """
            pattern = f"%_chunk_%"
            rows = await conn.fetch(query, pattern, str(doc_id))
            
            chunks = []
            for row in rows:
                doc = Document(
                    id=row['id'],
                    filename=row['filename'],
                    content=row['content'],
                    file_size=0,  # Không cần thiết cho chunks
                    embedding=None,  # Không cần thiết cho chunks
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    created_at=None,  # Không cần thiết cho chunks
                    updated_at=None,  # Không cần thiết cho chunks
                    status=FileStatus(row['status'])
                )
                chunks.append(doc)
            
            return chunks 
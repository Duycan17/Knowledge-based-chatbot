import os
import aiofiles
import asyncio
from typing import List, Dict, Any
from uuid import UUID, uuid4
import logging
from datetime import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from model.models import Document, FileStatus
from dbconnection.database import db_manager

logger = logging.getLogger(__name__)


class FileProcessingService:
    def __init__(self):
        from config.settings import settings
        self.max_file_size = settings.max_file_size
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.supported_extensions = {'.txt', '.md', '.csv', '.json', '.pdf'}
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )

    async def validate_file(self, filename: str, file_size: int) -> tuple[bool, str]:
        """Validate file upload"""
        if file_size > self.max_file_size:
            return False, f"File size exceeds limit of {self.max_file_size} bytes"
        
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in self.supported_extensions:
            return False, f"Unsupported file type. Supported: {', '.join(self.supported_extensions)}"
        
        return True, "File is valid"

    async def read_file_content(self, file_path: str, file_ext: str) -> str:
        """Đọc nội dung file"""
        if file_ext == '.pdf':
            return await self._extract_pdf_text(file_path)
        else:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return content

    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text từ PDF file"""
        try:
            from pypdf import PdfReader
            
            # Read PDF file
            reader = PdfReader(file_path)
            text_content = []
            
            # Extract text from each page
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text.strip():  # Only add non-empty pages
                    text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
            
            # Join all pages
            full_text = "\n\n".join(text_content)
            
            if not full_text.strip():
                raise ValueError("No text content found in PDF")
            
            logger.info(f"Extracted text from PDF with {len(reader.pages)} pages")
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    async def process_file(self, file_path: str, filename: str, file_size: int) -> Document:
        """Process file và tạo document"""
        # Get file extension
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Read file content
        content = await self.read_file_content(file_path, file_ext)
        
        # Create document
        doc_id = uuid4()
        document = Document(
            id=doc_id,
            filename=filename,
            content=content,
            file_size=file_size,
            metadata={
                "upload_time": datetime.utcnow().isoformat(),
                "file_path": file_path,
                "file_type": file_ext,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            },
            status=FileStatus.PROCESSING
        )
        
        # Save to database
        await db_manager.insert_document(document)
        
        # Process in background
        asyncio.create_task(self._process_document_async(document))
        
        return document

    async def _process_document_async(self, document: Document):
        """Process document trong background"""
        try:
            logger.info(f"Starting to process document {document.id}")
            
            # Update status to processing
            await db_manager.update_document(document.id, metadata={
                **document.metadata,
                "processing_started": datetime.utcnow().isoformat()
            })
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(document.content)
            logger.info(f"Split document into {len(chunks)} chunks")
            
            # Generate embeddings for chunks
            from .embedding_service import EmbeddingService
            embeddings_service = EmbeddingService()
            embeddings = await embeddings_service.generate_embeddings(chunks)
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Store chunks as separate documents
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_doc = Document(
                    id=uuid4(),
                    filename=f"{document.filename}_chunk_{i}",
                    content=chunk,
                    file_size=len(chunk.encode('utf-8')),
                    embedding=embedding,
                    metadata={
                        **document.metadata,
                        "parent_document_id": str(document.id),
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    },
                    status=FileStatus.COMPLETED
                )
                await db_manager.insert_document(chunk_doc)
                logger.info(f"Stored chunk {i} for document {document.id}")
            
            # Update original document status to completed
            await db_manager.update_document(document.id, metadata={
                **document.metadata,
                "processing_completed": datetime.utcnow().isoformat(),
                "total_chunks": len(chunks)
            })
            
            # Update status field to completed
            await db_manager.update_document_status(document.id, FileStatus.COMPLETED)
            
            logger.info(f"Document {document.id} processed successfully with {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Error processing document {document.id}: {e}")
            await db_manager.update_document(document.id, metadata={
                **document.metadata,
                "processing_error": str(e),
                "processing_failed": datetime.utcnow().isoformat()
            })
            await db_manager.update_document_status(document.id, FileStatus.FAILED)


 
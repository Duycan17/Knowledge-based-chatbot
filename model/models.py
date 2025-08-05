from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from enum import Enum


class FileStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentBase(BaseModel):
    filename: str = Field(..., description="Tên file gốc")
    content: str = Field(..., description="Nội dung file text")
    file_size: int = Field(..., description="Kích thước file tính bằng bytes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata bổ sung")


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: FileStatus = FileStatus.COMPLETED

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    size: int


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    chat_id: UUID
    response: str
    retrieved_docs: List[Dict[str, Any]] = Field(default_factory=list)


class AuditLogResponse(BaseModel):
    chat_id: UUID
    question: str
    response: str
    retrieved_docs: List[Dict[str, Any]]
    latency_ms: int
    timestamp: datetime
    feedback: Optional[str] = None
    model_confidence: Optional[float] = None

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    file_id: UUID
    filename: str
    status: FileStatus
    message: str
    file_size: int


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int


class BatchDeleteResponse(BaseModel):
    message: str
    results: Dict[str, Any]


class BatchUploadResponse(BaseModel):
    message: str
    total_files: int
    successful_uploads: int
    failed_uploads: int
    uploads: List[UploadResponse]
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# Database Models (for SQLAlchemy if needed)
class Document:
    def __init__(
        self,
        id: UUID,
        filename: str,
        content: str,
        file_size: int,
        embedding: Optional[List[float]] = None,
        metadata: Dict[str, Any] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
        status: FileStatus = FileStatus.COMPLETED
    ):
        self.id = id
        self.filename = filename
        self.content = content
        self.file_size = file_size
        self.embedding = embedding
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.status = status


class AuditLog:
    def __init__(
        self,
        chat_id: UUID,
        question: str,
        response: str,
        retrieved_docs: List[Dict[str, Any]],
        latency_ms: int,
        timestamp: datetime = None,
        feedback: Optional[str] = None,
        model_confidence: Optional[float] = None
    ):
        self.chat_id = chat_id
        self.question = question
        self.response = response
        self.retrieved_docs = retrieved_docs
        self.latency_ms = latency_ms
        self.timestamp = timestamp or datetime.utcnow()
        self.feedback = feedback
        self.model_confidence = model_confidence 
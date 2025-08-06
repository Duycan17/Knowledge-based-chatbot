import logging
from fastapi import FastAPI, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from typing import List

from dbconnection.database import db_manager
from service.knowledge_base_service import KnowledgeBaseService
from api.routes import APIRoutes
from model.models import ChatRequest
# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Knowledge Base API",
    description="AI-powered knowledge base system with file upload and RAG capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
knowledge_base_service = KnowledgeBaseService()
api_routes = APIRoutes(knowledge_base_service)


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    try:
        await db_manager.connect()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    try:
        await db_manager.disconnect()
        logger.info("Application shutdown successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Knowledge Base API is running", "status": "healthy"}


# @app.post("/knowledge/upload")
# async def upload_file(background_tasks, file):
#     """Upload file endpoint"""
#     return await api_routes.upload_file(background_tasks, file)


# @app.post("/knowledge/upload/batch")
# async def upload_multiple_files(background_tasks, files):
#     """Upload multiple files endpoint"""
#     return await api_routes.upload_multiple_files(background_tasks, files)

@app.post("/knowledge/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload file endpoint"""
    return await api_routes.upload_file(background_tasks, file)

@app.post("/knowledge/upload/batch")
async def upload_multiple_files(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """Upload multiple files endpoint"""
    return await api_routes.upload_multiple_files(background_tasks, files)

@app.get("/knowledge")
async def get_documents(page: int = 1, size: int = 10):
    """Get documents endpoint"""
    return await api_routes.get_documents(page, size)


@app.get("/knowledge/{doc_id}")
async def get_document(doc_id):
    """Get document endpoint"""
    return await api_routes.get_document(doc_id)


@app.get("/knowledge/{doc_id}/chunks")
async def get_document_chunks(doc_id):
    """Get document chunks endpoint"""
    return await api_routes.get_document_chunks(doc_id)


@app.put("/knowledge/{doc_id}")
async def update_document(doc_id, content: str = None, metadata: dict = None):
    """Update document endpoint"""
    return await api_routes.update_document(doc_id, content, metadata)


@app.delete("/knowledge/{doc_id}")
async def delete_document(doc_id):
    """Delete document endpoint"""
    return await api_routes.delete_document(doc_id)


@app.delete("/knowledge/batch")
async def delete_multiple_documents(doc_ids):
    """Delete multiple documents endpoint"""
    return await api_routes.delete_multiple_documents(doc_ids)


@app.post("/knowledge/{doc_id}/retry")
async def retry_document_processing(doc_id):
    """Retry document processing endpoint"""
    return await api_routes.retry_document_processing(doc_id)


@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint"""
    return await api_routes.chat(request)


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Chat streaming endpoint"""
    return await api_routes.chat_stream(request)


@app.get("/audit/{chat_id}")
async def get_audit_log(chat_id):
    """Get audit log endpoint"""
    return await api_routes.get_audit_log(chat_id)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
# Knowledge Base API

Hệ thống knowledge base containerized sử dụng FastAPI, Neon PostgreSQL với pgvector extension, LangChain và Gemini API. Hỗ trợ upload file text và RAG (Retrieval-Augmented Generation).

## 🚀 Features

- **File Upload**: Upload và process file text (.txt, .md, .csv, .json, .pdf)
- **Vector Search**: Similarity search với pgvector
- **RAG Pipeline**: Retrieval-Augmented Generation với Gemini
- **Audit Logging**: Log tất cả chat interactions
- **Async Processing**: Background processing cho file uploads
- **Document Management**: Xóa documents và chunks từ cả database và file system
- **Batch Operations**: Xóa nhiều documents cùng lúc
- **Docker Support**: Containerized với docker-compose

## 🛠️ Tech Stack

- **Backend**: FastAPI với async I/O
- **Database**: Neon PostgreSQL với pgvector extension
- **AI/ML**: LangChain, Gemini API
- **Container**: Docker với docker-compose
- **Caching**: Redis (optional)

## 📋 Requirements

- Python 3.11+
- Docker & Docker Compose
- Neon PostgreSQL account
- Google AI API key

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd knowledge-base-api
```

### 2. Environment Variables
Tạo file `.env`:
```bash
# Neon PostgreSQL
NEON_DATABASE_URL=postgresql://user:password@host:port/database

# Google AI
GOOGLE_API_KEY=your_google_api_key

# Optional Redis
REDIS_URL=redis://redis:6379

# File Processing
MAX_FILE_SIZE=10485760  # 10MB
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### 3. Run with Docker
```bash
# Build và start services
docker-compose up --build

# Run in background
docker-compose up -d
```

### 4. Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

## 📚 API Documentation

### File Upload & Knowledge Management

#### POST /knowledge/upload
Upload file text và process thành embeddings.

**Request:**
```bash
curl -X POST "http://localhost:8000/knowledge/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.txt"

# Hoặc upload PDF
curl -X POST "http://localhost:8000/knowledge/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "file_id": "uuid",
  "filename": "document.txt",
  "status": "processing",
  "message": "File uploaded successfully and processing started",
  "file_size": 1024
}
```

#### POST /knowledge/upload/batch
Upload nhiều file text cùng lúc và process thành embeddings.

**Request:**
```bash
curl -X POST "http://localhost:8000/knowledge/upload/batch" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@document1.txt" \
  -F "files=@document2.txt" \
  -F "files=@document3.txt"
```

**Response:**
```json
{
  "message": "Batch upload completed. 2 successful, 1 failed",
  "total_files": 3,
  "successful_uploads": 2,
  "failed_uploads": 1,
  "uploads": [
    {
      "file_id": "uuid-1",
      "filename": "document1.txt",
      "status": "processing",
      "message": "File uploaded successfully and processing started",
      "file_size": 1024
    },
    {
      "file_id": "uuid-2",
      "filename": "document2.txt",
      "status": "processing",
      "message": "File uploaded successfully and processing started",
      "file_size": 2048
    }
  ],
  "errors": [
    {
      "filename": "document3.txt",
      "error": "File size too large"
    }
  ]
}
```

#### GET /knowledge
Lấy danh sách documents với pagination.

#### DELETE /knowledge/{doc_id}
Xóa document và tất cả chunks của nó từ cả database và file system.

**Request:**
```bash
curl -X DELETE "http://localhost:8000/knowledge/{doc_id}"
```

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

#### DELETE /knowledge/batch
Xóa nhiều documents cùng lúc.

**Request:**
```bash
curl -X DELETE "http://localhost:8000/knowledge/batch" \
  -H "Content-Type: application/json" \
  -d '["doc_id_1", "doc_id_2", "doc_id_3"]'
```

**Response:**
```json
{
  "message": "Batch delete completed. 2 successful, 1 failed",
  "results": {
    "successful": ["doc_id_1", "doc_id_2"],
    "failed": ["doc_id_3"],
    "total_requested": 3,
    "total_successful": 2,
    "total_failed": 1
  }
}
```

**Request:**
```bash
curl "http://localhost:8000/knowledge?page=1&size=10"
```

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "document.txt",
      "content": "file content...",
      "file_size": 1024,
      "metadata": {},
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "status": "completed"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 10
}
```

#### GET /knowledge/{doc_id}
Lấy document theo ID.

#### PUT /knowledge/{doc_id}
Cập nhật document.

#### DELETE /knowledge/{doc_id}
Xóa document.

### Chat Interface

#### POST /chat
Chat với knowledge base.

**Request:**
```json
{
  "question": "What is the main topic of the uploaded documents?",
  "chat_id": "optional-uuid"
}
```

**Response:**
```json
{
  "chat_id": "uuid",
  "response": "Based on the uploaded documents...",
  "retrieved_docs": [
    {
      "id": "uuid",
      "filename": "document.txt"
    }
  ]
}
```

#### GET /audit/{chat_id}
Lấy audit log cho chat session.

**Response:**
```json
{
  "chat_id": "uuid",
  "question": "What is the main topic?",
  "response": "Based on the documents...",
  "retrieved_docs": [
    {
      "id": "uuid",
      "filename": "document.txt"
    }
  ],
  "latency_ms": 450,
  "timestamp": "2024-01-01T00:00:00",
  "feedback": null,
  "model_confidence": 0.95
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEON_DATABASE_URL` | Neon PostgreSQL connection string | Required |
| `GOOGLE_API_KEY` | Google AI API key | Required |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `MAX_FILE_SIZE` | Maximum file upload size (bytes) | `10485760` (10MB) |
| `CHUNK_SIZE` | Text chunk size for processing | `1000` |
| `CHUNK_OVERLAP` | Chunk overlap size | `200` |
| `LOG_LEVEL` | Logging level | `INFO` |

### File Processing

- **Supported Formats**: `.txt`, `.md`, `.csv`, `.json`
- **Max File Size**: 10MB (configurable)
- **Chunking**: Configurable chunk size và overlap
- **Async Processing**: Background tasks cho file processing

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Neon PostgreSQL│    │   Redis Cache   │
│                 │    │  (with pgvector)│    │   (Optional)    │
│  - File Upload  │◄──►│  - Documents    │    │  - Embeddings   │
│  - Chat API     │    │  - Audit Logs   │    │  - Query Cache  │
│  - RAG Pipeline │    │  - Vector Index │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Gemini API    │
│  - Embeddings   │
│  - Generation   │
└─────────────────┘
```

## 📊 Performance

- **Target Latency**: < 500ms cho inputs < 500 tokens
- **Async I/O**: FastAPI async endpoints
- **Connection Pooling**: Database connection pooling
- **Vector Indexing**: HNSW index cho similarity search
- **Caching**: Redis cho frequently accessed data

## 🔍 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# Docker logs
docker-compose logs -f app

# Local logs
tail -f app.log
```

## 🧪 Testing

### Sample Requests

#### Upload File
```bash
# Create test file
echo "This is a test document about AI and machine learning." > test.txt

# Upload file
curl -X POST "http://localhost:8000/knowledge/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.txt"
```

#### Chat with Knowledge Base
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the main topic of the uploaded documents?"
  }'
```

#### Get Documents
```bash
curl "http://localhost:8000/knowledge?page=1&size=10"
```

## 🚀 Deployment

### Docker Deployment
```bash
# Production build
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f
```

### Environment Setup
1. Set up Neon PostgreSQL database
2. Enable pgvector extension
3. Configure environment variables
4. Deploy with Docker

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request # Knowledge-based-chatbot

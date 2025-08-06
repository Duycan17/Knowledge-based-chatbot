# Deployed Application: https://128.199.96.56:3001


https://github.com/user-attachments/assets/3b1111a3-adf4-41dd-91d8-24c8a22d7afa


## 📦 Submission Includes

- ✅ GitHub repository with:
  - Source code
  - `Dockerfile` and `docker-compose.yml`
  - `.env` file configuration
  - Setup instructions (`README.md`)
  - Sample API requests using cURL

---

## ⚙️ Setup Instructions

### 1. Clone the Repository


### 2. Create `.env` File

```env
# Neon PostgreSQL (remote DB)
NEON_DATABASE_URL="your_neon_connection_string"

# Google Generative AI
GOOGLE_API_KEY="your_google_api_key"
```

### 3. Run with Docker Compose

```bash
docker compose up --build
```

API will be served at: [http://localhost:8000](http://localhost:8000)

---

## 🧪 Sample API Requests

---

### 📁 Upload File

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.txt"
```

---

### 📂 Upload Multiple Files

```bash
curl -X POST http://localhost:8000/upload/batch \
  -F "files=@file1.txt" \
  -F "files=@file2.pdf" \
  -F "files=@file3.md"
```

---

### 📄 Get Documents (Paginated)

```bash
curl "http://localhost:8000/documents?page=1&size=10"
```

---

### 📄 Get Document by ID

```bash
curl "http://localhost:8000/documents/{document_id}"
```

---

### 🧩 Get Document Chunks

```bash
curl "http://localhost:8000/documents/{document_id}/chunks"
```

---

### ✏️ Update Document

```bash
curl -X PUT http://localhost:8000/documents/{document_id} \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated content",
    "metadata": {
      "key": "value"
    }
  }'
```

---

### ❌ Delete Document

```bash
curl -X DELETE http://localhost:8000/documents/{document_id}
```

---

### 🧹 Delete Multiple Documents

```bash
curl -X DELETE http://localhost:8000/documents/batch \
  -H "Content-Type: application/json" \
  -d '[
    "uuid1",
    "uuid2",
    "uuid3"
  ]'
```


---

## 🤖 AI Interaction

### 💬 Chat (Single Response)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is machine learning?"
  }'
```

---

### 📡 Chat (Streaming Response)

```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain neural networks",
    "stream": true
  }'
```

---

## 📜 Audit Logs

```bash
curl "http://localhost:8000/audit/{chat_id}"
```

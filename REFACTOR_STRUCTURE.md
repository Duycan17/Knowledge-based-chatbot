# Refactored Code Structure

## Tổng quan
Code đã được refactor thành các module nhỏ hơn để dễ quản lý, maintain và mở rộng.

## Cấu trúc thư mục mới

```
├── main.py                          # Entry point
├── config/                          # Configuration management
│   ├── __init__.py
│   └── settings.py                  # Application settings
├── api/                             # API layer
│   ├── __init__.py
│   └── routes.py                    # API routes
├── service/                         # Business logic layer
│   ├── __init__.py
│   ├── knowledge_base_service.py    # Main service orchestrator
│   ├── file_processor.py            # File processing logic
│   ├── embedding_service.py         # Embedding generation
│   └── ai_service.py                # AI/ML operations
├── dbconnection/                    # Database layer
│   ├── __init__.py
│   ├── database.py                  # Main database manager
│   ├── connection.py                # Database connection
│   ├── schema.py                    # Database schema
│   ├── document_repository.py       # Document operations
│   └── audit_repository.py          # Audit operations
├── model/                           # Data models
│   ├── __init__.py
│   └── models.py                    # Pydantic models
├── utils/                           # Utility functions
│   ├── __init__.py
│   └── file_utils.py                # File operations
└── requirements.txt                 # Dependencies
```

## Chi tiết các module

### 1. Config Module (`config/`)
- **settings.py**: Quản lý tất cả configuration từ environment variables
- Sử dụng Pydantic BaseSettings để validation
- Centralized configuration management

### 2. API Module (`api/`)
- **routes.py**: Chứa tất cả API endpoints
- Tách biệt business logic khỏi HTTP layer
- Clean separation of concerns

### 3. Service Module (`service/`)
- **knowledge_base_service.py**: Main orchestrator cho business logic
- **file_processor.py**: Xử lý file upload và processing
- **embedding_service.py**: Generate embeddings
- **ai_service.py**: AI operations và chat functionality

### 4. Database Module (`dbconnection/`)
- **database.py**: Main database manager
- **connection.py**: Database connection management
- **schema.py**: Database schema creation
- **document_repository.py**: Document CRUD operations
- **audit_repository.py**: Audit log operations

### 5. Utils Module (`utils/`)
- **file_utils.py**: File system operations
- Reusable utility functions
- Centralized file operations

## Lợi ích của refactoring

### 1. **Separation of Concerns**
- Mỗi module có trách nhiệm rõ ràng
- Dễ dàng test từng component riêng biệt
- Giảm coupling giữa các components

### 2. **Maintainability**
- Code dễ đọc và hiểu hơn
- Dễ dàng thêm tính năng mới
- Dễ dàng sửa lỗi

### 3. **Scalability**
- Có thể mở rộng từng module độc lập
- Dễ dàng thêm new services
- Modular architecture

### 4. **Testability**
- Mỗi module có thể test riêng biệt
- Mock dependencies dễ dàng
- Unit tests và integration tests

### 5. **Configuration Management**
- Centralized settings
- Environment-specific configuration
- Type-safe configuration

## Dependency Flow

```
main.py
├── api/routes.py
│   └── service/knowledge_base_service.py
│       ├── service/file_processor.py
│       ├── service/embedding_service.py
│       └── service/ai_service.py
├── dbconnection/database.py
│   ├── dbconnection/document_repository.py
│   └── dbconnection/audit_repository.py
└── config/settings.py
```

## Migration Guide

### Từ cấu trúc cũ sang mới:

1. **Service Layer**:
   - `services.py` → `service/` module
   - Tách thành các service riêng biệt

2. **Database Layer**:
   - `database.py` → `dbconnection/` module
   - Tách thành connection, schema, repositories

3. **API Layer**:
   - Routes trong `main.py` → `api/routes.py`
   - Clean separation

4. **Configuration**:
   - Environment variables → `config/settings.py`
   - Type-safe configuration

## Best Practices Applied

1. **Dependency Injection**: Services inject dependencies
2. **Repository Pattern**: Database operations trong repositories
3. **Service Layer Pattern**: Business logic trong services
4. **Configuration Pattern**: Centralized configuration
5. **Utility Pattern**: Reusable utility functions

## Testing Strategy

1. **Unit Tests**: Test từng module riêng biệt
2. **Integration Tests**: Test interaction giữa modules
3. **API Tests**: Test endpoints
4. **Database Tests**: Test repositories

## Performance Benefits

1. **Lazy Loading**: Import modules khi cần
2. **Memory Efficiency**: Smaller modules
3. **Caching**: Configuration caching
4. **Connection Pooling**: Database connection pooling

## Security Improvements

1. **Input Validation**: Centralized validation
2. **Error Handling**: Proper error handling
3. **Logging**: Structured logging
4. **Configuration Security**: Secure configuration management 
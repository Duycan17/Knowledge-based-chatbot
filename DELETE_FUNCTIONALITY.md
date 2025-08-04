# Delete Functionality Documentation

## Tổng quan
Đã cải thiện chức năng delete để xóa hoàn toàn corpus và chunks của nó từ cả file system và database.

## Các thay đổi chính

### 1. Database Layer (`dbconnection/database.py`)
- **Cải thiện hàm `delete_document()`**:
  - Xóa tất cả chunks của document trước khi xóa document gốc
  - Sử dụng transaction để đảm bảo tính nhất quán
  - Thêm logging chi tiết cho quá trình xóa
  - Xử lý lỗi tốt hơn

```python
async def delete_document(self, doc_id: UUID) -> bool:
    """Xóa document theo ID và tất cả chunks của nó"""
    async with self.pool.acquire() as conn:
        async with conn.transaction():
            # Xóa chunks trước
            chunks_query = """
                DELETE FROM documents 
                WHERE filename LIKE $1 AND metadata->>'parent_document_id' = $2
            """
            # Xóa document gốc
            query = "DELETE FROM documents WHERE id = $1"
```

### 2. Service Layer (`service/services.py`)
- **Cải thiện hàm `delete_document()`**:
  - Lấy thông tin document trước khi xóa
  - Xóa file từ file system
  - Xử lý lỗi khi file không tồn tại
  - Thêm logging chi tiết

- **Thêm hàm `delete_multiple_documents()`**:
  - Xóa nhiều documents cùng lúc
  - Trả về kết quả chi tiết cho từng document
  - Xử lý lỗi riêng biệt cho từng document

### 3. API Layer (`main.py`)
- **Cải thiện endpoint `DELETE /knowledge/{doc_id}`**:
  - Xử lý lỗi tốt hơn
  - Trả về thông báo rõ ràng

- **Thêm endpoint `DELETE /knowledge/batch`**:
  - Xóa nhiều documents cùng lúc
  - Validation input (tối đa 100 documents)
  - Loại bỏ duplicate IDs
  - Trả về kết quả chi tiết

### 4. Model Layer (`model/models.py`)
- **Thêm `BatchDeleteResponse`**:
  - Model cho response của batch delete
  - Bao gồm thông tin chi tiết về kết quả

## Cách sử dụng

### Xóa một document
```bash
curl -X DELETE "http://localhost:8000/knowledge/{doc_id}"
```

### Xóa nhiều documents
```bash
curl -X DELETE "http://localhost:8000/knowledge/batch" \
  -H "Content-Type: application/json" \
  -d '["doc_id_1", "doc_id_2", "doc_id_3"]'
```

## Response format

### Single delete
```json
{
  "message": "Document deleted successfully"
}
```

### Batch delete
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

## Tính năng bảo mật và validation

1. **Transaction safety**: Sử dụng database transaction để đảm bảo tính nhất quán
2. **File system safety**: Kiểm tra file tồn tại trước khi xóa
3. **Input validation**: 
   - Kiểm tra document tồn tại
   - Giới hạn số lượng documents trong batch delete (tối đa 100)
   - Loại bỏ duplicate IDs
4. **Error handling**: 
   - Xử lý lỗi riêng biệt cho từng document trong batch
   - Không fail toàn bộ operation nếu một document lỗi
5. **Logging**: Ghi log chi tiết cho debugging và monitoring

## Database Schema
Chunks được lưu trữ trong cùng bảng `documents` với:
- `filename`: Pattern `%_chunk_%`
- `metadata.parent_document_id`: ID của document gốc
- `metadata.chunk_index`: Thứ tự của chunk

## Performance Considerations
- Sử dụng transaction để đảm bảo ACID properties
- Xóa chunks trước document gốc để tránh orphaned chunks
- Batch delete có thể xử lý tối đa 100 documents cùng lúc
- File system operations được thực hiện sau khi database operations thành công 
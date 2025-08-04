import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def create_upload_directory(upload_dir: str) -> None:
    """Tạo thư mục upload nếu chưa tồn tại"""
    try:
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"Upload directory created/verified: {upload_dir}")
    except Exception as e:
        logger.error(f"Error creating upload directory {upload_dir}: {e}")
        raise


def generate_safe_filename(original_filename: str) -> str:
    """Tạo tên file an toàn"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = "".join(c for c in original_filename if c.isalnum() or c in ('.-_')).rstrip()
    return f"{timestamp}_{safe_filename}"


def get_file_path(upload_dir: str, filename: str) -> str:
    """Tạo đường dẫn file đầy đủ"""
    return os.path.join(upload_dir, filename)


def delete_file_safely(file_path: str) -> bool:
    """Xóa file một cách an toàn"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
            return True
        else:
            logger.warning(f"File not found: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return False


def validate_file_extension(filename: str, supported_extensions: set) -> bool:
    """Validate file extension"""
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in supported_extensions


def validate_file_size(file_size: int, max_size: int) -> bool:
    """Validate file size"""
    return file_size <= max_size 
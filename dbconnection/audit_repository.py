import json
import logging
from typing import Optional
from uuid import UUID

from model.models import AuditLog

logger = logging.getLogger(__name__)


class AuditRepository:
    def __init__(self, pool):
        self.pool = pool

    async def insert_audit_log(self, audit_log: AuditLog):
        """Thêm audit log"""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO audit_logs (chat_id, question, response, retrieved_docs, latency_ms, timestamp, feedback, model_confidence)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """
            await conn.execute(
                query,
                audit_log.chat_id,
                audit_log.question,
                audit_log.response,
                json.dumps(audit_log.retrieved_docs),
                audit_log.latency_ms,
                audit_log.timestamp,
                audit_log.feedback,
                audit_log.model_confidence
            )

    async def get_audit_log(self, chat_id: UUID) -> Optional[AuditLog]:
        """Lấy audit log theo chat_id"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT chat_id, question, response, retrieved_docs, latency_ms, timestamp, feedback, model_confidence
                FROM audit_logs WHERE chat_id = $1
            """
            row = await conn.fetchrow(query, chat_id)
            if row:
                return AuditLog(
                    chat_id=row['chat_id'],
                    question=row['question'],
                    response=row['response'],
                    retrieved_docs=json.loads(row['retrieved_docs']) if row['retrieved_docs'] else [],
                    latency_ms=row['latency_ms'],
                    timestamp=row['timestamp'],
                    feedback=row['feedback'],
                    model_confidence=row['model_confidence']
                )
            return None 
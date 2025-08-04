import os
from typing import List
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        from config.settings import settings
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required")
        
        os.environ["GOOGLE_API_KEY"] = settings.google_api_key
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            task_type="retrieval_document"
        )

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings cho list texts"""
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding cho single text"""
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise 
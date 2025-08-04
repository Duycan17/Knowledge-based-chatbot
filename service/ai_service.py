import os
from typing import List
import logging
from google import genai

from model.models import Document
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        from config.settings import settings
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required")
        
        self.client = genai.Client()
        self.embeddings_service = EmbeddingService()

    async def generate_response(self, question: str, context_docs: List[Document]) -> str:
        """Generate response với context từ documents"""
        try:
            # Prepare context
            context = self._prepare_context(context_docs)
            
            # Generate response với Gemini
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Context from knowledge base:
            {context}
            
            Question: {question}
            
            Please provide a comprehensive answer based on the context provided. 
            If the context doesn't contain relevant information, please say so.
            """
            
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Sorry, I encountered an error while processing your question: {str(e)}"

    def _prepare_context(self, documents: List[Document]) -> str:
        """Prepare context từ documents"""
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"Document {i} ({doc.filename}):\n{doc.content}\n")
        
        return "\n".join(context_parts)

    async def search_relevant_documents(self, question: str, limit: int = 5) -> List[Document]:
        """Tìm documents liên quan dựa trên question"""
        try:
            # Generate embedding cho question
            question_embedding = await self.embeddings_service.generate_embedding(question)
            
            # Search similar documents
            from dbconnection.database import db_manager
            similar_docs = await db_manager.search_similar_documents(question_embedding, limit)
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return [] 
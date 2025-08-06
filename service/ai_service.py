import logging
import json
import asyncio
import time
from typing import List, AsyncGenerator
import redis.asyncio as redis

import google.generativeai as genai

from model.models import Document
from .embedding_service import EmbeddingService
from config.settings import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required")

        self.embeddings_service = EmbeddingService()
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")  # or "gemini-1.5-flash-latest"

        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True
        )

    async def generate_response(self, question: str, context_docs: List[Document]) -> str:
        start_time = time.time()

        try:
            cache_key = f"response:{hash(question)}"
            cached_response = await self.redis_client.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit for question: {question[:50]}...")
                return cached_response

            context = await self._prepare_optimized_context(context_docs, settings.max_context_tokens)
            response = await self._generate_ai_response(question, context)

            await self.redis_client.setex(cache_key, settings.cache_ttl_response, response)

            response_time = time.time() - start_time
            await self._log_response_time(response_time, len(context_docs))

            return response

        except Exception as e:
            response_time = time.time() - start_time
            await self._log_error_response_time(response_time)
            logger.error(f"Error generating response: {e}")
            return f"Sorry, I encountered an error while processing your question: {str(e)}"

    async def generate_streaming_response(self, question: str, context_docs: List[Document]) -> AsyncGenerator[str, None]:
        """Generate streaming response using Gemini, yielding chunks of text."""
        start_time = time.time()

        try:
            context = await self._prepare_optimized_context(context_docs, settings.max_context_tokens)
            
            # Create streaming response
            prompt = f"""Context: {context}
Q: {question}
A:"""

            try:
                # Use streaming generation
                response = self.model.generate_content(
                    prompt,
                    stream=True,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        top_p=0.8,
                        top_k=40,
                        max_output_tokens=2048,
                    )
                )
                
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                        
            except Exception as e:
                logger.error(f"Error during streaming AI response generation: {e}")
                yield f"Sorry, I encountered an error while processing your question: {str(e)}"

            response_time = time.time() - start_time
            await self._log_response_time(response_time, len(context_docs))

        except Exception as e:
            response_time = time.time() - start_time
            await self._log_error_response_time(response_time)
            logger.error(f"Error generating streaming response: {e}")
            yield f"Sorry, I encountered an error while processing your question: {str(e)}"

    async def _generate_ai_response(self, question: str, context: str) -> str:
        prompt = f"""Context: {context}
Q: {question}
A:"""

        try:
            # Gemini Flash 2.5 requires async call
            response = await self.model.generate_content_async(prompt)
            return "".join([part.text for part in response.parts]) if response.parts else "No response."
        except Exception as e:
            logger.error(f"Error during AI response generation: {e}")
            raise

    async def _prepare_optimized_context(self, documents: List[Document], max_tokens: int = 4000) -> str:
        if not documents:
            return "No relevant documents found."

        context_parts = []
        current_tokens = 0

        for doc in documents:
            doc_tokens = len(doc.content.split())
            if current_tokens + doc_tokens > max_tokens:
                break
            context_parts.append(f"Document ({doc.filename}):\n{doc.content}\n")
            current_tokens += doc_tokens

        return "\n".join(context_parts)

    async def search_relevant_documents(self, question: str, limit: int = 5) -> List[Document]:
        try:
            cache_key = f"search:{hash(question)}:{limit}"
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for search: {question[:50]}...")
                # Reconstruct Document objects from dicts
                docs_data = json.loads(cached_result)
                return [Document(**doc_data) for doc_data in docs_data]

            tasks = [
                self.embeddings_service.generate_embedding(question),
                self._prepare_search_context(question)
            ]
            question_embedding, _ = await asyncio.gather(*tasks)

            from dbconnection.database import db_manager
            similar_docs = await db_manager.search_similar_documents(question_embedding, limit)

            await self.redis_client.setex(
                cache_key,
                settings.cache_ttl_search,
                json.dumps([
                    {
                        'id': str(doc.id),
                        'filename': doc.filename,
                        'content': doc.content,
                        'file_size': doc.file_size,
                        'metadata': doc.metadata,
                        'status': doc.status.value if hasattr(doc.status, 'value') else doc.status
                    } for doc in similar_docs
                ])
            )

            return similar_docs

        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []

    async def _prepare_search_context(self, question: str) -> str:
        return f"Searching for documents related to: {question}"

    async def _log_response_time(self, response_time: float, num_docs: int):
        logger.info(f"Response generated in {response_time:.2f}s with {num_docs} documents")

    async def _log_error_response_time(self, response_time: float):
        logger.error(f"Error response time: {response_time:.2f}s")

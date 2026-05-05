import os
import json
from openai import AsyncOpenAI
from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.EMBEDDING_API_KEY)
        self.model = settings.EMBEDDING_MODEL

    async def get_embeddings(self, texts: list, model: str = None) -> list:
        """
        Fetch embeddings for a list of texts using the specified model.
        """
        try:
            target_model = model or self.model
            response = await self.client.embeddings.create(input=texts, model=target_model)
            embeddings = [data.embedding for data in response.data]
            
            return embeddings
        except Exception as e:
            print(f"Error getting embeddings: {e}")
            return []

embedding_service = EmbeddingService()

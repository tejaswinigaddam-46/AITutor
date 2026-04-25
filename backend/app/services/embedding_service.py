import os
import json
from openai import OpenAI
from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.EMBEDDING_API_KEY)
        self.model = settings.EMBEDDING_MODEL

    async def get_embeddings(self, texts: list, model: str = None) -> list:
        """
        Fetch embeddings for a list of texts using the specified model.
        """
        try:
            target_model = model or self.model
            response = self.client.embeddings.create(input=texts, model=target_model)
            embeddings = [data.embedding for data in response.data]
            
            # COMMENT: To extract embeddings to a file for debugging
            # with open("debug_embeddings.json", "w") as f:
            #     json.dump(embeddings, f)
            
            return embeddings
        except Exception as e:
            print(f"Error getting embeddings: {e}")
            return []

embedding_service = EmbeddingService()

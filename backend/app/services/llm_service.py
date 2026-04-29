import os
import json
import logging
from openai import AsyncOpenAI
from app.core.config import settings
from app.db.conversation_store import conversation_store

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # Initialize OpenAI-compatible client for xAI
        self.client = AsyncOpenAI(
            api_key=settings.XAI_API_KEY,
            base_url="https://api.x.ai/v1"
        )
        self.model = settings.LLM_MODEL

    async def generate_response(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        temperature: float = 0.2, 
        messages: list = None,
        response_format: dict = None
    ):
        """
        Generates a response from the LLM based on system and user prompts.
        Supports structured output via response_format.
        """
        try:
            if not messages:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            
            if response_format:
                params["response_format"] = response_format

            #print(f"\n--- DEBUG: LLM INPUT PROMPT ---\n{json.dumps(messages, indent=2)}\n-------------------------------\n")
            response = await self.client.chat.completions.create(**params)
            content = response.choices[0].message.content
            conversation_store.update_api_count()
            #print(f"\n--- DEBUG: LLM OUTPUT RESPONSE ---\n{content}\n----------------------------------\n")
            return content
        except Exception as e:
            logger.error(f"Error generating response from LLM: {e}")
            return f"Error: {str(e)}"

llm_service = LLMService()

import os
import json
import logging
from typing import Any, Dict, Type, Callable
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError
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

    async def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: dict,
        validation_model: Type[BaseModel],
        refusal_checker: Callable[[Dict], bool],
        refusal_handler: Callable[[Dict, Any], Any],
        success_handler: Callable[[BaseModel, Any], Any],
        retries: int = 2,
        temperature: float = 0.2
    ) -> Any:
        """
        Generic method for LLM calling that handles:
        - Retries
        - JSON parsing
        - Validation
        - Refusal handling
        """
        last_error = ""
        for attempt in range(retries):
            attempt_num = attempt + 1
            logger.info(f"Fetching structured response... Attempt {attempt_num}/{retries}")
            try:
                answer_raw = await self.generate_response(
                    system_prompt,
                    user_prompt,
                    temperature=temperature,
                    response_format=response_format
                )

                # Parse JSON response
                try:
                    answer_data = json.loads(answer_raw)
                except json.JSONDecodeError as e:
                    last_error = f"JSON Decode Error: {str(e)}"
                    logger.warning(f"Attempt {attempt_num} failed: {last_error}")
                    continue

                # Check for refusal
                if refusal_checker(answer_data):
                    logger.info(f"LLM refused to answer on attempt {attempt_num}")
                    return refusal_handler(answer_data)

                # Validate with Pydantic
                try:
                    validated_answer = validation_model(**answer_data)
                    logger.info(f"Successfully fetched and validated API response on attempt {attempt_num}")
                    return success_handler(validated_answer)
                except ValidationError as ve:
                    last_error = f"Validation Error: {str(ve)}"
                    logger.warning(f"Attempt {attempt_num} failed: {last_error}")
                    continue

            except Exception as e:
                last_error = f"Unexpected Error: {str(e)}"
                logger.error(f"Attempt {attempt_num} failed: {last_error}")
                if attempt == retries - 1:
                    break

        raise Exception(f"Failed to generate a valid response after {retries} attempts. Last error: {last_error}")


llm_service = LLMService()

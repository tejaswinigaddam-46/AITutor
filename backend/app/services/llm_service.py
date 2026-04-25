import os
import json
from openai import OpenAI
from app.core.config import settings

class LLMService:
    def __init__(self):
        # Initialize Groq client using OpenAI SDK compatibility
        self.client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = settings.LLM_MODEL

    async def generate_response(self, system_prompt: str, user_prompt: str, temperature: float = 0.2):
        """
        Generates a response from the LLM based on system and user prompts.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            answer = response.choices[0].message.content
            
            # COMMENT: To extract LLM response to a file for debugging
            # with open("debug_llm_response.txt", "w") as f:
            #     f.write(answer)
                
            return answer
        except Exception as e:
            print(f"Error generating response from LLM: {e}")
            return f"Error: {str(e)}"

llm_service = LLMService()

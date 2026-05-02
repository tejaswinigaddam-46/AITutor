
from typing import Callable, Dict, Type
from pydantic import BaseModel
from app.schemas.rag import AITutorResponse
from app.services.SelfLearningPrompt import TUTOR_SYSTEM_PROMPT, TUTOR_RESPONSE_FORMAT

class LLMConfig:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        response_format: Dict,
        validation_model: Type[BaseModel],
        user_prompt_builder: Callable,
        refusal_handler: Callable
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.response_format = response_format
        self.validation_model = validation_model
        self.user_prompt_builder = user_prompt_builder
        self.refusal_handler = refusal_handler


def build_tutor_user_prompt(context_text: str, prev_summary: str, question: str) -> str:
    user_prompt = f"Context:\n{context_text}\n\n"
    if prev_summary:
        user_prompt += f"Previous Conversation Summary (prev_summary):\n{prev_summary}\n\n"
    user_prompt += f"Question: {question}\n\nAnswer:"
    return user_prompt


def handle_tutor_refusal(answer_data: dict, context_chunks: list) -> dict:
    refusal_msg = answer_data.get("message", "I'm here to help you learn your subject 😊 Let's focus on your lesson.")
    refusal_summary = answer_data.get("summary", "Refused due to safety/scope")
    return {
        "answer": refusal_msg,
        "sources": context_chunks,
        "summary": refusal_summary
    }


tutor_config = LLMConfig(
    name="tutor",
    system_prompt=TUTOR_SYSTEM_PROMPT,
    response_format=TUTOR_RESPONSE_FORMAT,
    validation_model=AITutorResponse,
    user_prompt_builder=build_tutor_user_prompt,
    refusal_handler=handle_tutor_refusal
)

# You can add more configs here, e.g.:
# from app.services.TeacherGuidedPrompt import TEACHER_GUIDED_SYSTEM_PROMPT, TEACHER_GUIDED_RESPONSE_FORMAT
# teacher_guided_config = LLMConfig(...)

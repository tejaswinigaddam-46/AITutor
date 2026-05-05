import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.modules.llm.llm_service import llm_service
from app.modules.orchestration.rag_service import rag_service
from app.schemas.rag import TeacherFeedbackOverviewResponse

logger = logging.getLogger(__name__)

class TeacherFeedbackService:
    def __init__(self) -> None:
        self._prompt_file_path = (
            Path(__file__).resolve().parents[1] / "llm" / "prompts" / "TeachersFeedbackOverivePrompt.py"
        )

    def _load_prompt_template_and_format(self) -> tuple[str, Dict[str, Any]]:
        raw = self._prompt_file_path.read_text(encoding="utf-8")

        template_match = re.search(r"FeedbackOverivePrompt\s*=\s*f'''([\s\S]*?)'''", raw)
        if not template_match:
            raise ValueError("Could not find FeedbackOverivePrompt template in TeachersFeedbackOverivePrompt.py")

        template = template_match.group(1)

        format_match = re.search(r"response_format\s*=\s*(\{[\s\S]*\})\s*$", raw)
        if not format_match:
            raise ValueError("Could not find response_format JSON in TeachersFeedbackOverivePrompt.py")

        response_format_json = format_match.group(1)
        response_format = json.loads(response_format_json)

        return template, response_format

    async def generate_feedback_overview(
        self,
        topic: str,
        no_of_chunks: int = 5,
        book_name: Optional[str] = None,
        retries: int = 2,
        conversation_id: Optional[UUID] = None,
        username: Optional[str] = None,
    ) -> dict:
        retrieval = await rag_service.retrieve_context(
            question=topic,
            limit=no_of_chunks,
            book_name=book_name,
            conversation_id=conversation_id,
            username=username,
        )

        if not retrieval["ok"]:
            return {
                "answer": retrieval["error"],
                "sources": [],
            }

        context_text = retrieval["context_text"]
        context_chunks = retrieval["context_chunks"]

        template, response_format = self._load_prompt_template_and_format()
        response_format_str = json.dumps(response_format, ensure_ascii=False)

        user_prompt = template.format(
            topic=topic,
            retrieved_text_from_RAG=context_text,
            response_format=response_format_str,
        )

        system_prompt = "You are an academic planning assistant."

        result = await llm_service.generate_structured_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format=response_format,
            validation_model=TeacherFeedbackOverviewResponse,
            refusal_checker=lambda data: data.get("status") == "refused",
            refusal_handler=lambda data: {
                "answer": data.get("message", "Refused"),
                "sources": context_chunks,
            },
            success_handler=lambda validated: {
                "answer": validated,
                "sources": context_chunks,
            },
            retries=retries,
        )

        return result


teacher_feedback_service = TeacherFeedbackService()

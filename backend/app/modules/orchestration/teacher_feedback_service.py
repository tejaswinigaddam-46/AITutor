import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.modules.llm.llm_service import llm_service
from app.modules.orchestration.rag_service import rag_service
from app.modules.persistence.question_store import question_store
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

    def _resolve_question_id(
        self,
        topic: str,
        student_username: Optional[str],
        book_name: Optional[str],
    ) -> Optional[int]:
        if not student_username or not book_name:
            return None

        assignments = question_store.get_question_assignments(student_username=student_username)
        if not assignments:
            return None

        assignments = [
            a for a in assignments if str(a.get("curriculum_book_name") or "") == str(book_name)
        ]
        if not assignments:
            return None

        normalized_topic = (topic or "").strip().casefold()

        exact = [
            a
            for a in assignments
            if str(a.get("question_name") or "").strip().casefold() == normalized_topic
        ]
        if exact:
            return exact[0].get("question_id")

        if len(assignments) == 1:
            return assignments[0].get("question_id")

        scored: List[Tuple[float, dict]] = []
        for a in assignments:
            qname = str(a.get("question_name") or "").strip()
            qnorm = qname.casefold()
            score = 0.0
            if normalized_topic and normalized_topic in qnorm:
                score = len(normalized_topic) / max(len(qnorm), 1)
            elif qnorm and qnorm in normalized_topic:
                score = len(qnorm) / max(len(normalized_topic), 1)

            if score > 0:
                scored.append((score, a))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1].get("question_id")

        return None

    def _persist_feedback_overview_subtopics(
        self,
        result: dict,
        topic: str,
        book_name: Optional[str],
        username: Optional[str],
    ) -> None:
        answer = result.get("answer")
        if not isinstance(answer, TeacherFeedbackOverviewResponse):
            return

        question_id = self._resolve_question_id(
            topic=topic,
            student_username=username,
            book_name=book_name,
        )
        if not question_id:
            logger.warning(
                "Skipping subtopic persistence: no matching question assignment for topic=%s student=%s book=%s",
                topic,
                username,
                book_name,
            )
            return

        subtopic_names = [
            item.subtopic.strip()
            for item in answer.answer_plan
            if item.subtopic and item.subtopic.strip()
        ]
        if not subtopic_names:
            return

        try:
            question_store.create_question_subtopics_and_progress(
                question_id=question_id,
                subtopic_names=subtopic_names,
                default_status="in_progress",
            )
        except Exception:
            logger.exception(
                "Failed persisting feedback overview subtopics for question_id=%s",
                question_id,
            )

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
        self._persist_feedback_overview_subtopics(
            result=result,
            topic=topic,
            book_name=book_name,
            username=username,
        )
        return result


teacher_feedback_service = TeacherFeedbackService()

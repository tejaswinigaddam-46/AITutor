import logging
import json
from typing import List, Optional
from uuid import UUID
from app.modules.persistence.question_store import question_store
from app.modules.orchestration.conversation_service import conversation_service
from app.modules.orchestration.rag_service import rag_service

logger = logging.getLogger(__name__)


class QuestionSubtopicService:
    def create_question_subtopic(
        self,
        question_id: int,
        subtopic_name: str
    ) -> dict:
        if not subtopic_name or not subtopic_name.strip():
            raise ValueError("Subtopic name cannot be empty")
        
        question = question_store.get_question_assignment(question_id)
        if not question:
            raise ValueError(f"Question assignment with id {question_id} not found")
        
        return question_store.create_question_subtopic(
            question_id=question_id,
            subtopic_name=subtopic_name
        )

    def get_question_subtopics(self, question_id: int) -> List[dict]:
        return question_store.get_question_subtopics(question_id)

    def get_question_subtopic(self, question_subtopics_id: int) -> Optional[dict]:
        return question_store.get_question_subtopic(question_subtopics_id)

    def update_question_subtopic(
        self,
        question_subtopics_id: int,
        subtopic_name: Optional[str] = None
    ) -> Optional[dict]:
        if subtopic_name and not subtopic_name.strip():
            raise ValueError("Subtopic name cannot be empty")
        
        return question_store.update_question_subtopic(
            question_subtopics_id=question_subtopics_id,
            subtopic_name=subtopic_name
        )

    def delete_question_subtopic(self, question_subtopics_id: int) -> bool:
        return question_store.delete_question_subtopic(question_subtopics_id)

    def create_question_progress(
        self,
        question_subtopics_id: int,
        student_username: str,
        status: str = 'yet_to_start'
    ) -> dict:
        if not student_username or not student_username.strip():
            raise ValueError("Student username cannot be empty")
        valid_statuses = ['yet_to_start', 'in_progress', 'completed', 'learning']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        return question_store.create_question_progress(
            question_subtopics_id=question_subtopics_id,
            student_username=student_username,
            status=status
        )

    def get_question_progress(self, question_subtopics_id: int) -> Optional[dict]:
        return question_store.get_question_progress(question_subtopics_id)

    def get_all_question_progress(self) -> List[dict]:
        return question_store.get_all_question_progress()

    def update_question_progress(
        self,
        question_subtopics_id: int,
        status: str
    ) -> Optional[dict]:
        valid_statuses = ['yet_to_start', 'in_progress', 'completed', 'learning']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        return question_store.update_question_progress(
            question_subtopics_id=question_subtopics_id,
            status=status
        )

    def delete_question_progress(self, question_subtopics_id: int) -> bool:
        return question_store.delete_question_progress(question_subtopics_id)

    def get_question_subtopics_with_progress(self, question_id: int) -> List[dict]:
        return question_store.get_question_subtopics_with_progress(question_id)

    async def request_subtopic(
        self,
        question_subtopics_id: int,
        username: str,
        question: Optional[str] = None,
    ) -> dict:
        logger.info(
            "request_subtopic: start question_subtopics_id=%s username=%s has_question=%s",
            question_subtopics_id,
            username,
            bool((question or "").strip()),
        )
        subtopic = question_store.get_question_subtopic(question_subtopics_id)
        if not subtopic:
            logger.info(
                "request_subtopic: subtopic not found question_subtopics_id=%s",
                question_subtopics_id,
            )
            raise ValueError(f"Question subtopic with id {question_subtopics_id} not found")

        question_id = subtopic.get("question_id")
        logger.info(
            "request_subtopic: loaded subtopic question_subtopics_id=%s question_id=%s conversation_id_present=%s",
            question_subtopics_id,
            question_id,
            bool(subtopic.get("conversation_id")),
        )
        assignment = question_store.get_question_assignment(question_id)
        if not assignment:
            logger.info(
                "request_subtopic: assignment not found question_id=%s (from question_subtopics_id=%s)",
                question_id,
                question_subtopics_id,
            )
            raise ValueError(f"Question assignment with id {question_id} not found")

        curriculum_book_name = assignment.get("curriculum_book_name")
        question_name = str(assignment.get("question_name") or "").strip()
        logger.info(
            "request_subtopic: loaded assignment question_id=%s curriculum_book_name=%s question_name_present=%s",
            question_id,
            curriculum_book_name,
            bool(question_name),
        )

        subtopic_name = str(subtopic.get("subtopic_name") or "").strip()
        prompt = (question or "").strip()
        if not prompt:
            if question_name:
                prompt = f"Explain the subtopic '{subtopic_name}' for the question '{question_name}'."
            else:
                prompt = f"Explain the subtopic '{subtopic_name}'."
        logger.info(
            "request_subtopic: prepared prompt question_subtopics_id=%s subtopic_name=%s prompt_len=%s",
            question_subtopics_id,
            subtopic_name,
            len(prompt),
        )

        subtopic_conversation_id = subtopic.get("conversation_id")

        if subtopic_conversation_id:
            conversation_id = UUID(str(subtopic_conversation_id))
            logger.info(
                "request_subtopic: reusing conversation_id=%s for question_subtopics_id=%s",
                conversation_id,
                question_subtopics_id,
            )
            await conversation_service.create_message(
                username=username,
                conversation_id=conversation_id,
                role="user",
                content=prompt,
                curriculum_book_name=curriculum_book_name,
                title=subtopic_name,
            )
            logger.info(
                "request_subtopic: saved user message conversation_id=%s question_subtopics_id=%s",
                conversation_id,
                question_subtopics_id,
            )
        else:
            logger.info(
                "request_subtopic: creating new conversation for question_subtopics_id=%s",
                question_subtopics_id,
            )
            user_msg, _ = await conversation_service.create_message(
                username=username,
                conversation_id=None,
                role="user",
                content=prompt,
                curriculum_book_name=curriculum_book_name,
                title=subtopic_name,
            )
            conversation_id = UUID(str(user_msg["conversation_id"]))
            logger.info(
                "request_subtopic: created conversation_id=%s for question_subtopics_id=%s; persisting to question_subtopics",
                conversation_id,
                question_subtopics_id,
            )
            subtopic = question_store.update_question_subtopic_conversation_id(
                question_subtopics_id=question_subtopics_id,
                conversation_id=str(conversation_id),
            )
            if not subtopic:
                logger.info(
                    "request_subtopic: failed to persist conversation_id for question_subtopics_id=%s",
                    question_subtopics_id,
                )
                raise ValueError(f"Question subtopic with id {question_subtopics_id} not found")
            logger.info(
                "request_subtopic: persisted conversation_id=%s to question_subtopics_id=%s",
                subtopic.get("conversation_id"),
                question_subtopics_id,
            )

        logger.info(
            "request_subtopic: calling ai question_subtopics_id=%s conversation_id=%s book=%s",
            question_subtopics_id,
            conversation_id,
            curriculum_book_name,
        )
        result = await rag_service.answer_query(
            question=prompt,
            book_name=curriculum_book_name,
            conversation_id=conversation_id,
            username=username,
        )
        logger.info(
            "request_subtopic: ai call done question_subtopics_id=%s conversation_id=%s has_answer=%s has_summary=%s sources_count=%s",
            question_subtopics_id,
            conversation_id,
            bool(result.get("answer") is not None),
            bool(result.get("summary")),
            len(result.get("sources") or []),
        )

        answer_obj = result.get("answer")
        if hasattr(answer_obj, "model_dump"):
            assistant_payload = answer_obj.model_dump()
        elif hasattr(answer_obj, "dict"):
            assistant_payload = answer_obj.dict()
        else:
            assistant_payload = answer_obj

        if isinstance(assistant_payload, (dict, list)):
            assistant_content = json.dumps(assistant_payload, ensure_ascii=False)
        else:
            assistant_content = str(assistant_payload)

        logger.info(
            "request_subtopic: saving assistant message question_subtopics_id=%s conversation_id=%s assistant_content_len=%s",
            question_subtopics_id,
            conversation_id,
            len(assistant_content),
        )
        await conversation_service.create_message(
            username=username,
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_content,
            curriculum_book_name=curriculum_book_name,
            summary=result.get("summary"),
            title=subtopic_name,
        )
        logger.info(
            "request_subtopic: completed question_subtopics_id=%s conversation_id=%s",
            question_subtopics_id,
            conversation_id,
        )

        return {
            "question_subtopics_id": subtopic["question_subtopics_id"],
            "question_id": subtopic["question_id"],
            "subtopic_name": subtopic["subtopic_name"],
            "conversation_id": conversation_id,
            "ai": result,
        }


question_subtopic_service = QuestionSubtopicService()

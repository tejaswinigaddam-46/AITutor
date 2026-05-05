import logging
from typing import Optional
from uuid import UUID

from app.modules.llm.llm_service import llm_service
from app.modules.llm.llm_configs import tutor_config
from app.modules.orchestration.rag_service import rag_service

logger = logging.getLogger(__name__)


class SelfLearningService:
    async def answer_query(
        self,
        question: str,
        limit: int = 5,
        book_name: str = None,
        retries: int = 2,
        conversation_id: Optional[UUID] = None,
        username: Optional[str] = None,
    ):
        retrieval = await rag_service.retrieve_context(
            question=question,
            limit=limit,
            book_name=book_name,
            conversation_id=conversation_id,
            username=username,
        )

        if not retrieval["ok"]:
            msg = retrieval["error"]
            if msg == "No context found":
                return {
                    "answer": "I'm sorry, I couldn't find any relevant information in the database to answer your question.",
                    "sources": [],
                    "summary": "No context found",
                }
            return {
                "answer": "Error generating query embedding",
                "sources": [],
                "summary": "Error: Embedding failed",
            }

        prev_summary = retrieval["prev_summary"]
        context_chunks = retrieval["context_chunks"]
        context_text = retrieval["context_text"]

        user_prompt = tutor_config.user_prompt_builder(context_text, prev_summary, question)

        try:
            result = await llm_service.generate_structured_response(
                system_prompt=tutor_config.system_prompt,
                user_prompt=user_prompt,
                response_format=tutor_config.response_format,
                validation_model=tutor_config.validation_model,
                refusal_checker=lambda data: data.get("status") == "refused",
                refusal_handler=lambda data: tutor_config.refusal_handler(data, context_chunks),
                success_handler=lambda validated: {
                    "answer": validated,
                    "sources": context_chunks,
                    "summary": validated.summary,
                },
                retries=retries,
            )
            return result
        except Exception as e:
            logger.error(f"Error in self learning service: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "sources": context_chunks,
            }


self_learning_service = SelfLearningService()

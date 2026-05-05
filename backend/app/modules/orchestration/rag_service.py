import logging
from typing import Optional, List
from uuid import UUID
from app.modules.rag.embedding_service import embedding_service
from app.modules.rag.vector_store import vector_store
from app.modules.persistence.conversation_store import conversation_store

logger = logging.getLogger(__name__)

class RAGService:
    async def retrieve_context(
        self,
        question: str,
        limit: int = 5,
        book_name: str = None,
        conversation_id: Optional[UUID] = None,
        username: Optional[str] = None,
    ) -> dict:
        prev_summary = None
        convo_book_name = book_name
        conversation_history: List[dict] = []

        if conversation_id and username:
            convo = conversation_store.get_conversation(conversation_id, username)
            if convo:
                convo_book_name = convo.get("curriculum_book_name")

            messages = conversation_store.get_messages(conversation_id, username)
            if messages:
                conversation_history = messages
                for m in reversed(messages):
                    if m.get("summary"):
                        prev_summary = m["summary"]
                        break

        embedding_query = question
        if prev_summary:
            embedding_query = f"{prev_summary}\n\n{question}"

        query_embeddings = await embedding_service.get_embeddings([embedding_query])
        if not query_embeddings:
            return {
                "ok": False,
                "error": "Error generating query embedding",
                "context_chunks": [],
                "context_text": "",
                "prev_summary": prev_summary,
                "book_name": convo_book_name,
            }

        query_vector = query_embeddings[0]
        context_chunks = vector_store.similarity_search(query_vector, limit=limit, book_name=convo_book_name)

        if not context_chunks:
            return {
                "ok": False,
                "error": "No context found",
                "context_chunks": [],
                "context_text": "",
                "prev_summary": prev_summary,
                "book_name": convo_book_name,
            }

        context_text = "\n\n".join(
            [
                f"Source: {c['book_name']}, Ch: {c['chapter']}, Page: {c['page_number']}\nContent: {c['content']}"
                for c in context_chunks
            ]
        )

        return {
            "ok": True,
            "error": None,
            "context_chunks": context_chunks,
            "context_text": context_text,
            "prev_summary": prev_summary,
            "book_name": convo_book_name,
            "conversation_history": conversation_history,
        }

    async def answer_query(
        self, 
        question: str, 
        limit: int = 5, 
        book_name: str = None, 
        retries: int = 2,
        conversation_id: Optional[UUID] = None,
        username: Optional[str] = None
    ):
        """
        Main function to retrieve chunks and get an answer from the LLM using structured outputs.
        """
        from app.modules.orchestration.self_learning_service import self_learning_service

        return await self_learning_service.answer_query(
            question=question,
            limit=limit,
            book_name=book_name,
            retries=retries,
            conversation_id=conversation_id,
            username=username,
        )

rag_service = RAGService()

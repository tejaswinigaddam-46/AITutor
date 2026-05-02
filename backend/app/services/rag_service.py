import logging
from typing import Optional, List
from uuid import UUID
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service
from app.services.llm_configs import tutor_config
from app.db.vector_store import vector_store
from app.db.conversation_store import conversation_store

logger = logging.getLogger(__name__)

class RAGService:
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
        # 0. Get previous summary and conversation history
        prev_summary = None
        convo_book_name = book_name
        conversation_history: List[dict] = []
        
        if conversation_id and username:
            convo = conversation_store.get_conversation(conversation_id, username)
            if convo:
                convo_book_name = convo.get('curriculum_book_name')
                
            messages = conversation_store.get_messages(conversation_id, username)
            if messages:
                conversation_history = messages
                # Get the summary from the most recent message that has one
                for m in reversed(messages):
                    if m.get('summary'):
                        prev_summary = m['summary']
                        break

        # 1. Prepare query for embedding: use summary + question if we have a summary
        embedding_query = question
        if prev_summary:
            embedding_query = f"{prev_summary}\n\n{question}"
            
        query_embeddings = await embedding_service.get_embeddings([embedding_query])
        if not query_embeddings:
            return {
                "answer": "Error generating query embedding", 
                "sources": [],
                "summary": "Error: Embedding failed"
            }
        
        query_vector = query_embeddings[0]
        
        # 2. Search vector store
        context_chunks = vector_store.similarity_search(query_vector, limit=limit, book_name=convo_book_name)
        
        if not context_chunks:
            return {
                "answer": "I'm sorry, I couldn't find any relevant information in the database to answer your question.",
                "sources": [],
                "summary": "No context found"
            }

        # 3. Augment prompt with context
        context_text = "\n\n".join([
            f"Source: {c['book_name']}, Ch: {c['chapter']}, Page: {c['page_number']}\nContent: {c['content']}" 
            for c in context_chunks
        ])

        # Use config to build user prompt
        user_prompt = tutor_config.user_prompt_builder(context_text, prev_summary, question)

        # 4. Generate answer via LLM using the generic method
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
                    "summary": validated.summary
                },
                retries=retries
            )
            print(f"DEBUG: Final RAG Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in RAG service: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "sources": context_chunks
            }

rag_service = RAGService()

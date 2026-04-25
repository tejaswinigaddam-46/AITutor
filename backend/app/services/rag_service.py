import json
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service
from app.db.vector_store import vector_store

class RAGService:
    async def answer_query(self, query_text: str, limit: int = 5, book_name: str = None):
        """
        Main function to retrieve chunks and get an answer from the LLM.
        """
        # 1. Embed query
        query_embeddings = await embedding_service.get_embeddings([query_text])
        if not query_embeddings:
            return {"answer": "Error generating query embedding", "sources": []}
        
        query_vector = query_embeddings[0]
        
        # 2. Search vector store
        context_chunks = vector_store.similarity_search(query_vector, limit=limit, book_name=book_name)
        
        # COMMENT: To extract retrieved chunks to a file for debugging
        # with open("debug_retrieved_chunks.json", "w") as f:
        #     json.dump(context_chunks, f, indent=2)

        if not context_chunks:
            return {
                "answer": "I'm sorry, I couldn't find any relevant information in the database to answer your question.",
                "sources": []
            }

        # 3. Augment prompt with context
        context_text = "\n\n".join([
            f"Source: {c['book_name']}, Ch: {c['chapter']}, Page: {c['page_number']}\nContent: {c['content']}" 
            for c in context_chunks
        ])

        system_prompt = (
            "You are a helpful AI Tutor. Use the provided context from textbooks to answer the user's question. "
            "If the answer is not in the context, say that you don't have enough information from the textbooks. "
            "Always be concise and educational."
        )
        
        user_prompt = f"Context:\n{context_text}\n\nQuestion: {query_text}\n\nAnswer:"

        # 4. Generate answer via LLM
        answer = await llm_service.generate_response(system_prompt, user_prompt)
        
        return {
            "answer": answer,
            "sources": context_chunks
        }

rag_service = RAGService()

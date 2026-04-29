import json
import logging
from typing import Optional
from uuid import UUID
from pydantic import ValidationError
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service
from app.db.vector_store import vector_store
from app.db.conversation_store import conversation_store
from app.services.conversation_service import conversation_service
from app.schemas.rag import AITutorResponse

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
        # 0. Get previous summary from conversation history
        prev_summary = None
        convo_book_name = book_name
        
        if conversation_id and username:
            convo = conversation_store.get_conversation(conversation_id, username)
            if convo:
                convo_book_name = convo.get('curriculum_book_name')
                
            messages = conversation_store.get_messages(conversation_id, username)
            if messages:
                # Get the summary from the most recent message that has one
                for m in reversed(messages):
                    if m.get('summary'):
                        prev_summary = m['summary']
                        break

        # 1. Embed query
        query_embeddings = await embedding_service.get_embeddings([question])
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

        system_prompt = (
            '''You are a safe AI Tutor for students (age 10–16). Teach clearly using textbook context only.

### INPUT
* Textbook Content (Context)
* Student Question

---

### 🚫 SAFETY (HIGHEST PRIORITY)
Refuse if question is:

* Non-educational (sports scores, movies, gossip)
* Harmful/illegal (violence, hacking, drugs)
* Inappropriate (sexual, abusive)
* Out-of-scope (not from textbook)

**Response (strict):**
"I'm here to help you learn your subject 😊 Let's focus on your lesson."

---

### 📘 TEACHING METHOD

#### 1. LAYERED TEACHING (MANDATORY)
** Get the textbook points**

* **TEXTBOOK_POINTS (VERY IMPORTANT)**
list the points from textbook as is. later Explain in normal language (simple_explanation). and after explaining all points give brief examples reexplaining same concept by dry running through the example (example).

Example Logic (Crucial):
Show the "Before" and "After" clearly so the student can see the change.

---

#### 2. SMART SECTIONS (remove only if not needed)
* Memory Trick → Dont create new use only existing worldwide patterns or examples 
* Why → to improves understanding (why_it_works)
* Practice → 3 MCQs per subtopic

#### 3. TOPIC CHUNKING
* Topic breakdown
* Current subtopic (meaningful description)

### 🚫 SAFETY
Refuse if question is non-educational or out-of-scope.
Response: status="refused", message="I'm here to help you learn your subject 😊 Let's focus on your lesson.", summary="Refused due to safety/scope"

### SUMMARY (MANDATORY)
Include a detailed summary of the current exact topic (max 1000 words) in the "summary" field.
'''
        )
        
        # Prepare user prompt with summaries
        user_prompt = f"Context:\n{context_text}\n\n"
        if prev_summary:
            user_prompt += f"prev summary: {prev_summary}\n"
        
        user_prompt += f"\nQuestion: {question}\n\nAnswer:"
        
        # Define the JSON schema for structured output
        # Using AITutorResponse.model_json_schema() or manual schema as requested by user
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "tutor_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "message": {"type": "string"},
                        "topic_breakdown": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "current_subtopic": {"type": "string"},
                        "textbook_points": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "simple_explanation": {"type": "string"},
                        "example": {"type": "string"},
                        "memory_trick": {"type": "string"},
                        "why_it_works": {"type": "string"},
                        "practice": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "question": {"type": "string"},
                                    "options": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "string"},
                                                "text": {"type": "string"}
                                            },
                                            "required": ["id", "text"],
                                            "additionalProperties": False
                                        }
                                    },
                                    "correct_answer": {"type": "string"},
                                    "explanation": {"type": "string"}
                                },
                                "required": ["question", "options", "correct_answer", "explanation"],
                                "additionalProperties": False
                            }
                        },
                        "next_step": {"type": "string"},
                        "summary": {"type": "string"}
                    },
                    "required": [
                        "status", "message", "topic_breakdown", "current_subtopic",
                        "textbook_points", "simple_explanation", "example",
                        "memory_trick", "why_it_works", "practice", "next_step",
                        "summary"
                    ],
                    "additionalProperties": False
                }
            }
        }

        # 4. Generate answer via LLM with structured output
        last_error = ""
        for attempt in range(retries):
            attempt_num = attempt + 1
            logger.info(f"Fetching structured response... Attempt {attempt_num}/{retries} for question: {question[:50]}...")
            try:
                answer_raw = await llm_service.generate_response(
                    system_prompt, 
                    user_prompt, 
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
                if answer_data.get("status") == "refused":
                    logger.info(f"LLM refused to answer on attempt {attempt_num}")
                    return {
                        "answer": answer_data.get("message", "I'm here to help you learn your subject 😊 Let's focus on your lesson."),
                        "sources": context_chunks,
                        "summary": answer_data.get("summary", "Refused")
                    }

                # Validate with Pydantic
                try:
                    validated_answer = AITutorResponse(**answer_data)
                    logger.info(f"Successfully fetched and validated API response on attempt {attempt_num}")
                    
                    # 5. Save interaction to database if in a conversation
                    if conversation_id and username:
                        try:
                            # Save user message (without summary for now, or we could use the turn summary)
                            await conversation_service.create_message(
                                username=username,
                                conversation_id=conversation_id,
                                role="user",
                                content=question,
                                curriculum_book_name=convo_book_name or "GOV_SSC_PHYSICS", 
                                summary=None 
                            )
                            
                            # Save assistant message with summary
                            await conversation_service.create_message(
                                username=username,
                                conversation_id=conversation_id,
                                role="assistant",
                                content=json.dumps(answer_data), 
                                curriculum_book_name=convo_book_name or "GOV_SSC_PHYSICS",
                                summary=validated_answer.summary
                            )
                        except Exception as save_err:
                            logger.error(f"Error saving interaction to DB: {save_err}")

                    result = {
                        "answer": validated_answer,
                        "sources": context_chunks,
                        "summary": validated_answer.summary
                    }
                    print(f"DEBUG: Final RAG Result: {result}")
                    return result
                except ValidationError as ve:
                    last_error = f"Validation Error: {str(ve)}"
                    logger.warning(f"Attempt {attempt_num} failed: {last_error}")
                    continue
                    
            except Exception as e:
                last_error = f"Unexpected Error: {str(e)}"
                logger.error(f"Attempt {attempt_num} failed: {last_error}")
                if attempt == retries - 1:
                    break

        return {
            "answer": f"Error: Failed to generate a valid response after {retries} attempts. Last error: {last_error}",
            "sources": context_chunks
        }

rag_service = RAGService()

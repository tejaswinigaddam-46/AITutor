from fastapi import APIRouter, Depends, HTTPException
from app.schemas.rag import Query, Answer
from app.modules.orchestration.rag_service import rag_service
from app.core.security import get_current_username

router = APIRouter()

@router.post("/query", response_model=Answer)
async def ask_question(
    query: Query,
    username: str = Depends(get_current_username)
):
    try:
        result = await rag_service.answer_query(
            query.question, 
            conversation_id=query.conversation_id,
            username=username
        )
        print(f"DEBUG: RAG Answer result: {result}")
        return result
    except Exception as e:
        print(f"DEBUG: RAG Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

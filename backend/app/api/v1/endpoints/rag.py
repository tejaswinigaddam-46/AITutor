from fastapi import APIRouter, Depends, HTTPException
from app.schemas.rag import Query, Answer
from app.services.rag_service import rag_service

router = APIRouter()

@router.post("/query", response_model=Answer)
async def ask_question(query: Query):
    try:
        result = await rag_service.answer_query(query.question)
        print(f"DEBUG: RAG Answer result: {result}")
        return result
    except Exception as e:
        print(f"DEBUG: RAG Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

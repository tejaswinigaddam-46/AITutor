from fastapi import APIRouter, Depends, HTTPException
from app.schemas.rag import Query, Answer, FeedbackOverviewQuery, FeedbackOverviewAnswer
from app.modules.orchestration.rag_service import rag_service
from app.modules.orchestration.teacher_feedback_service import teacher_feedback_service
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
            book_name=query.book_name,
            conversation_id=query.conversation_id,
            username=username
        )
        print(f"DEBUG: RAG Answer result: {result}")
        return result
    except Exception as e:
        print(f"DEBUG: RAG Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback-overview", response_model=FeedbackOverviewAnswer)
async def generate_feedback_overview(
    query: FeedbackOverviewQuery,
    username: str = Depends(get_current_username),
):
    try:
        result = await teacher_feedback_service.generate_feedback_overview(
            topic=query.topic,
            no_of_chunks=8,
            book_name=query.book_name,
            conversation_id=query.conversation_id,
            username=username,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

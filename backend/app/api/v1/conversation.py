import logging
import json
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from uuid import UUID
from pydantic import BaseModel
from app.schemas.conversation import (
    MessageCreate, 
    MessageRead, 
    ConversationRead,
    ConversationAskRequest,
    ConversationAskResponse,
    ConversationFeedbackOverviewRequest,
    ConversationFeedbackOverviewResponse,
)
from app.modules.orchestration.conversation_service import conversation_service
from app.modules.orchestration.rag_service import rag_service
from app.modules.orchestration.teacher_feedback_service import teacher_feedback_service
from app.modules.persistence.question_store import question_store
from app.core.security import get_current_username

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/messages", response_model=MessageRead)
async def create_message(
    message_data: MessageCreate,
    username: str = Depends(get_current_username)
):
    try:
        message, is_new = await conversation_service.create_message(
            username=username,
            conversation_id=message_data.conversation_id,
            role=message_data.role,
            content=message_data.content,
            curriculum_book_name=message_data.curriculum_book_name,
            summary=message_data.summary,
            title=message_data.title,
            question_id=message_data.question_id,
            question_subtopics_id=message_data.question_subtopics_id,
        )
        logger.info(f"Created message: {message}")
        return message
    except ValueError as e:
        logger.warning(f"Error creating message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", response_model=ConversationAskResponse)
async def ask_and_save(
    request: ConversationAskRequest,
    username: str = Depends(get_current_username),
):
    try:
        user_title = request.title or request.question[:30]
        user_message, is_new_conversation = await conversation_service.create_message(
            username=username,
            conversation_id=request.conversation_id,
            role="user",
            content=request.question,
            curriculum_book_name=request.curriculum_book_name,
            title=user_title,
            question_id=request.question_id,
            question_subtopics_id=request.question_subtopics_id,
        )

        conversation_id_to_use = user_message.get("conversation_id")
        if isinstance(conversation_id_to_use, str):
            conversation_id_to_use = UUID(conversation_id_to_use)

        ai_result = await rag_service.answer_query(
            question=request.question,
            book_name=getattr(request.curriculum_book_name, "value", request.curriculum_book_name),
            conversation_id=conversation_id_to_use,
            username=username,
        )

        ai_answer = ai_result.get("answer")
        ai_summary = ai_result.get("summary")

        assistant_title = None
        if isinstance(ai_answer, BaseModel):
            assistant_content = ai_answer.model_dump_json()
            assistant_title = getattr(ai_answer, "current_subtopic", None)
            if not ai_summary:
                ai_summary = getattr(ai_answer, "summary", None)
        elif isinstance(ai_answer, (dict, list)):
            assistant_content = json.dumps(ai_answer, ensure_ascii=False)
            if isinstance(ai_answer, dict):
                assistant_title = ai_answer.get("current_subtopic") or ai_answer.get("topic") or ai_answer.get("title")
        else:
            assistant_content = "" if ai_answer is None else str(ai_answer)
            assistant_title = assistant_content[:50] if assistant_content else None

        if ai_summary is not None:
            ai_summary = str(ai_summary)[:200]
        if assistant_title is not None:
            assistant_title = str(assistant_title)[:50]

        assistant_message, _ = await conversation_service.create_message(
            username=username,
            conversation_id=conversation_id_to_use,
            role="assistant",
            content=assistant_content,
            curriculum_book_name=request.curriculum_book_name,
            summary=ai_summary,
            title=assistant_title,
            question_id=request.question_id,
            question_subtopics_id=request.question_subtopics_id,
        )

        return {
            "conversation_id": conversation_id_to_use,
            "is_new_conversation": is_new_conversation,
            "user_message": user_message,
            "ai": ai_result,
            "assistant_message": assistant_message,
        }
    except ValueError as e:
        logger.warning(f"Error creating conversation ask: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error in conversation ask: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback-overview", response_model=ConversationFeedbackOverviewResponse)
async def feedback_overview_and_save(
    request: ConversationFeedbackOverviewRequest,
    username: str = Depends(get_current_username),
):
    try:
        assignment = question_store.get_question_assignment(request.question_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Question assignment not found")

        topic = str(assignment.get("question_name") or "").strip()
        if not topic:
            raise HTTPException(status_code=400, detail="Question assignment has empty question_name")

        assignment_book_name = str(assignment.get("curriculum_book_name") or "").strip()
        request_book_name = getattr(request.curriculum_book_name, "value", request.curriculum_book_name)
        if assignment_book_name and request_book_name and str(assignment_book_name) != str(request_book_name):
            raise HTTPException(status_code=400, detail="curriculum_book_name does not match question assignment")

        user_title = request.title or topic[:30]
        user_message, is_new_conversation = await conversation_service.create_message(
            username=username,
            conversation_id=request.conversation_id,
            role="user",
            content=topic,
            curriculum_book_name=request.curriculum_book_name,
            title=user_title,
            question_id=request.question_id,
            question_subtopics_id=request.question_subtopics_id,
        )

        conversation_id_to_use = user_message.get("conversation_id")
        if isinstance(conversation_id_to_use, str):
            conversation_id_to_use = UUID(conversation_id_to_use)

        ai_result = await teacher_feedback_service.generate_feedback_overview(
            question_id=request.question_id,
            no_of_chunks=request.no_of_chunks,
            book_name=getattr(request.curriculum_book_name, "value", request.curriculum_book_name),
            conversation_id=conversation_id_to_use,
            username=username,
        )

        ai_answer = ai_result.get("answer")
        assistant_title = None
        if isinstance(ai_answer, BaseModel):
            assistant_content = ai_answer.model_dump_json()
            answer_plan = getattr(ai_answer, "answer_plan", None)
            if answer_plan and len(answer_plan) > 0:
                assistant_title = getattr(answer_plan[0], "subtopic", None)
        elif isinstance(ai_answer, (dict, list)):
            assistant_content = json.dumps(ai_answer, ensure_ascii=False)
        else:
            assistant_content = "" if ai_answer is None else str(ai_answer)

        if assistant_title is not None:
            assistant_title = str(assistant_title)[:50]

        assistant_message, _ = await conversation_service.create_message(
            username=username,
            conversation_id=conversation_id_to_use,
            role="assistant",
            content=assistant_content,
            curriculum_book_name=request.curriculum_book_name,
            summary=None,
            title=assistant_title,
            question_id=request.question_id,
            question_subtopics_id=request.question_subtopics_id,
        )

        return {
            "conversation_id": conversation_id_to_use,
            "is_new_conversation": is_new_conversation,
            "user_message": user_message,
            "ai": ai_result,
            "assistant_message": assistant_message,
        }
    except ValueError as e:
        logger.warning(f"Error creating feedback overview conversation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error in feedback overview conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ConversationRead])
async def list_conversations(username: str = Depends(get_current_username)):
    try:
        conversations = conversation_service.get_conversations(username)
        logger.info(f"List conversations for user {username}: {conversations}")
        return conversations
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-question/{question_id}", response_model=ConversationRead)
async def get_conversation_by_question(
    question_id: int,
    username: str = Depends(get_current_username),
):
    convo = conversation_service.get_conversation_by_question(username=username, question_id=question_id)
    logger.info(f"Get conversation by question_id={question_id}: {convo}")
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo

@router.get("/by-question-subtopic/{question_subtopics_id}", response_model=ConversationRead)
async def get_conversation_by_question_subtopic(
    question_subtopics_id: int,
    username: str = Depends(get_current_username),
):
    convo = conversation_service.get_conversation_by_question_subtopic(
        username=username,
        question_subtopics_id=question_subtopics_id,
    )
    logger.info(f"Get conversation by question_subtopics_id={question_subtopics_id}: {convo}")
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo

@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: UUID, 
    username: str = Depends(get_current_username)
):
    convo = conversation_service.get_conversation(conversation_id, username)
    logger.info(f"Get conversation {conversation_id}: {convo}")
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo

@router.get("/{conversation_id}/messages", response_model=List[MessageRead])
async def list_messages(
    conversation_id: UUID, 
    username: str = Depends(get_current_username)
):
    try:
        messages = conversation_service.get_messages(conversation_id, username)
        logger.info(f"List messages for conversation {conversation_id}: {messages}")
        return messages
    except Exception as e:
        logger.error(f"Error listing messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID, 
    username: str = Depends(get_current_username)
):
    success = conversation_service.delete_conversation(conversation_id, username)
    response = {"status": "success", "message": "Conversation deleted"}
    logger.info(f"Delete conversation {conversation_id} result: {success}, response: {response}")
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found or not owned by user")
    return response

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: UUID, 
    username: str = Depends(get_current_username)
):
    success = conversation_service.delete_message(message_id, username)
    response = {"status": "success", "message": "Message deleted"}
    logger.info(f"Delete message {message_id} result: {success}, response: {response}")
    if not success:
        raise HTTPException(status_code=404, detail="Message not found or not authorized")
    return response

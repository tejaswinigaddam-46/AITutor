from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from uuid import UUID
from app.schemas.conversation import (
    MessageCreate, 
    MessageRead, 
    ConversationRead,
)
from app.services.conversation_service import conversation_service
from app.core.security import get_current_username

router = APIRouter()

@router.post("/messages", response_model=MessageRead)
async def create_message(
    message_data: MessageCreate,
    username: str = Depends(get_current_username)
):
    try:
        message, is_new = conversation_service.create_message(
            username=username,
            conversation_id=message_data.conversation_id,
            role=message_data.role,
            content=message_data.content,
            curriculum_book_name=message_data.curriculum_book_name,
            title=message_data.title
        )
        print(f"DEBUG: Created message: {message}")
        return message
    except ValueError as e:
        print(f"DEBUG: Error creating message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"DEBUG: Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[ConversationRead])
async def list_conversations(username: str = Depends(get_current_username)):
    try:
        conversations = conversation_service.get_conversations(username)
        #print(f"DEBUG: List conversations for user {username}: {conversations}")
        return conversations
    except Exception as e:
        #print(f"DEBUG: Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: UUID, 
    username: str = Depends(get_current_username)
):
    convo = conversation_service.get_conversation(conversation_id, username)
    print(f"DEBUG: Get conversation {conversation_id}: {convo}")
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
        print(f"DEBUG: List messages for conversation {conversation_id}: {messages}")
        return messages
    except Exception as e:
        print(f"DEBUG: Error listing messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID, 
    username: str = Depends(get_current_username)
):
    success = conversation_service.delete_conversation(conversation_id, username)
    response = {"status": "success", "message": "Conversation deleted"}
    print(f"DEBUG: Delete conversation {conversation_id} result: {success}, response: {response}")
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
    print(f"DEBUG: Delete message {message_id} result: {success}, response: {response}")
    if not success:
        raise HTTPException(status_code=404, detail="Message not found or not authorized")
    return response

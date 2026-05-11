from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from enum import Enum
from app.schemas.rag import Answer, FeedbackOverviewAnswer

class CurriculumBookEnum(str, Enum):
    GOV_SSC_ENGLISH = "GOV_SSC_ENGLISH"
    GOV_SSC_PHYSICS = "GOV_SSC_PHYSICS"
    GOV_SSC_CHEMISTRY = "GOV_SSC_CHEMISTRY"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class MessageBase(BaseModel):
    role: MessageRole
    content: str

class MessageCreate(MessageBase):
    conversation_id: Optional[UUID] = None
    curriculum_book_name: CurriculumBookEnum
    title: Optional[str] = None
    summary: Optional[str] = None
    question_id: Optional[int] = None
    question_subtopics_id: Optional[int] = None

class MessageRead(MessageBase):
    id: UUID
    conversation_id: UUID
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    username: str
    curriculum_book_name: CurriculumBookEnum
    title: Optional[str] = None
    question_id: Optional[int] = None
    question_subtopics_id: Optional[int] = None

class ConversationRead(ConversationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationWithMessages(ConversationRead):
    messages: List[MessageRead]


class ConversationAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    curriculum_book_name: CurriculumBookEnum
    conversation_id: Optional[UUID] = None
    title: Optional[str] = None
    question_id: Optional[int] = None
    question_subtopics_id: Optional[int] = None


class ConversationAskResponse(BaseModel):
    conversation_id: UUID
    is_new_conversation: bool
    user_message: MessageRead
    ai: Answer
    assistant_message: MessageRead


class ConversationFeedbackOverviewRequest(BaseModel):
    question_id: int = Field(..., ge=1)
    curriculum_book_name: CurriculumBookEnum
    conversation_id: Optional[UUID] = None
    title: Optional[str] = None
    no_of_chunks: int = 8
    question_subtopics_id: Optional[int] = None


class ConversationFeedbackOverviewResponse(BaseModel):
    conversation_id: UUID
    is_new_conversation: bool
    user_message: MessageRead
    ai: FeedbackOverviewAnswer
    assistant_message: MessageRead

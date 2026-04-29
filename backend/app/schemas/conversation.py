from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from enum import Enum

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
    summary: Optional[str] = None

class MessageCreate(MessageBase):
    conversation_id: Optional[UUID] = None
    curriculum_book_name: CurriculumBookEnum
    title: Optional[str] = None

class MessageRead(MessageBase):
    id: UUID
    conversation_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    username: str
    curriculum_book_name: CurriculumBookEnum
    title: Optional[str] = None

class ConversationRead(ConversationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationWithMessages(ConversationRead):
    messages: List[MessageRead]

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class Query(BaseModel):
    question: str
    book_name: str
    conversation_id: Optional[UUID] = None

class Option(BaseModel):
    id: str
    text: str

class PracticeQuestion(BaseModel):
    question: str
    options: List[Option]
    correct_answer: str
    explanation: str

class AITutorResponse(BaseModel):
    status: str = Field(default="200")
    message: str = Field(default="Fetched successfully")
    topic_breakdown: List[str]
    current_subtopic: str
    textbook_points: List[str]
    simple_explanation: str
    example: str
    memory_trick: str
    why_it_works: str
    practice: List[PracticeQuestion]
    next_step: str
    summary: str = Field(..., description="Concise summary of the current interaction (max 20 words)")

class Source(BaseModel):
    id: int
    curriculum_book_name: str
    book_name: str | None = None
    chapter: str | None = None
    page_number: int | None = None
    content: str
    distance: float | None = None
    chunk_metadata: dict | None = None

class Answer(BaseModel):
    answer: AITutorResponse | str
    sources: List[Source]
    summary: Optional[str] = None


class TeacherFeedbackAnswerPlanItem(BaseModel):
    subtopic: str

    class Config:
        extra = "forbid"


class TeacherFeedbackOverviewResponse(BaseModel):
    topic: str
    answer_plan: List[TeacherFeedbackAnswerPlanItem] = Field(..., min_items=3)

    class Config:
        extra = "forbid"


class FeedbackOverviewQuery(BaseModel):
    topic: str
    no_of_chunks: int = 5
    book_name: str
    conversation_id: Optional[UUID] = None


class FeedbackOverviewAnswer(BaseModel):
    answer: TeacherFeedbackOverviewResponse | str
    sources: List[Source]

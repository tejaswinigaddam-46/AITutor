from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum
from uuid import UUID
from app.schemas.conversation import CurriculumBookEnum


class QuestionProgressStatus(str, Enum):
    YET_TO_START = "yet_to_start"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class QuestionOverallStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "InProgress"
    COMPLETED = "completed"


class QuestionAssignmentBase(BaseModel):
    question_name: str
    curriculum_book_name: CurriculumBookEnum
    student_username: str
    exam_id: UUID


class QuestionAssignmentCreate(QuestionAssignmentBase):
    pass


class QuestionAssignmentRead(QuestionAssignmentBase):
    question_id: int
    assigned_by_username: str
    assigned_at: datetime

    class Config:
        from_attributes = True


class QuestionSubtopicBase(BaseModel):
    question_id: int
    subtopic_name: str


class QuestionSubtopicCreate(QuestionSubtopicBase):
    pass


class QuestionSubtopicRead(QuestionSubtopicBase):
    question_subtopics_id: int

    class Config:
        from_attributes = True


class QuestionProgressBase(BaseModel):
    question_subtopics_id: int
    status: QuestionProgressStatus


class QuestionProgressCreate(QuestionProgressBase):
    student_username: str


class QuestionProgressUpdate(BaseModel):
    status: QuestionProgressStatus


class QuestionProgressRead(QuestionProgressBase):
    student_username: str
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestionSubtopicWithProgress(QuestionSubtopicRead):
    progress: Optional[QuestionProgressRead] = None


class QuestionAssignmentWithSubtopics(QuestionAssignmentRead):
    subtopics: List[QuestionSubtopicWithProgress]


class QuestionProgressSummary(BaseModel):
    question_id: int
    question_name: str
    status: QuestionOverallStatus

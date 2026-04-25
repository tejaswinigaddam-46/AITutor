from pydantic import BaseModel
from typing import List

class Query(BaseModel):
    text: str

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
    answer: str
    sources: List[Source]

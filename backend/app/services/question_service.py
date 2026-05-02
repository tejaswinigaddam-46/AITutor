from typing import List, Optional
from app.db.question_store import question_store


class QuestionService:
    def create_question_assignment(
        self,
        question_name: str,
        curriculum_book_name: str,
        student_username: str,
        assigned_by_username: str
    ) -> dict:
        if not question_name or not question_name.strip():
            raise ValueError("Question name cannot be empty")
        if not student_username or not student_username.strip():
            raise ValueError("Student username cannot be empty")
        
        return question_store.create_question_assignment(
            question_name=question_name,
            curriculum_book_name=curriculum_book_name,
            student_username=student_username,
            assigned_by_username=assigned_by_username
        )

    def get_question_assignments(
        self,
        student_username: Optional[str] = None,
        assigned_by_username: Optional[str] = None
    ) -> List[dict]:
        return question_store.get_question_assignments(
            student_username=student_username,
            assigned_by_username=assigned_by_username
        )

    def get_question_assignment(self, question_id: int) -> Optional[dict]:
        return question_store.get_question_assignment(question_id)

    def update_question_assignment(
        self,
        question_id: int,
        question_name: Optional[str] = None,
        curriculum_book_name: Optional[str] = None,
        student_username: Optional[str] = None
    ) -> Optional[dict]:
        if question_name and not question_name.strip():
            raise ValueError("Question name cannot be empty")
        if student_username and not student_username.strip():
            raise ValueError("Student username cannot be empty")
        
        return question_store.update_question_assignment(
            question_id=question_id,
            question_name=question_name,
            curriculum_book_name=curriculum_book_name,
            student_username=student_username
        )

    def delete_question_assignment(self, question_id: int) -> bool:
        return question_store.delete_question_assignment(question_id)


question_service = QuestionService()

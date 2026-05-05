from typing import List, Optional
from app.modules.persistence.question_store import question_store


class QuestionSubtopicService:
    def create_question_subtopic(
        self,
        question_id: int,
        subtopic_name: str
    ) -> dict:
        if not subtopic_name or not subtopic_name.strip():
            raise ValueError("Subtopic name cannot be empty")
        
        question = question_store.get_question_assignment(question_id)
        if not question:
            raise ValueError(f"Question assignment with id {question_id} not found")
        
        return question_store.create_question_subtopic(
            question_id=question_id,
            subtopic_name=subtopic_name
        )

    def get_question_subtopics(self, question_id: int) -> List[dict]:
        return question_store.get_question_subtopics(question_id)

    def get_question_subtopic(self, question_subtopics_id: int) -> Optional[dict]:
        return question_store.get_question_subtopic(question_subtopics_id)

    def update_question_subtopic(
        self,
        question_subtopics_id: int,
        subtopic_name: Optional[str] = None
    ) -> Optional[dict]:
        if subtopic_name and not subtopic_name.strip():
            raise ValueError("Subtopic name cannot be empty")
        
        return question_store.update_question_subtopic(
            question_subtopics_id=question_subtopics_id,
            subtopic_name=subtopic_name
        )

    def delete_question_subtopic(self, question_subtopics_id: int) -> bool:
        return question_store.delete_question_subtopic(question_subtopics_id)

    def create_question_progress(
        self,
        question_subtopics_id: int,
        student_username: str,
        status: str = 'yet_to_start'
    ) -> dict:
        if not student_username or not student_username.strip():
            raise ValueError("Student username cannot be empty")
        valid_statuses = ['yet_to_start', 'in_progress', 'completed']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        return question_store.create_question_progress(
            question_subtopics_id=question_subtopics_id,
            student_username=student_username,
            status=status
        )

    def get_question_progress(self, question_subtopics_id: int) -> Optional[dict]:
        return question_store.get_question_progress(question_subtopics_id)

    def get_all_question_progress(self) -> List[dict]:
        return question_store.get_all_question_progress()

    def update_question_progress(
        self,
        question_subtopics_id: int,
        status: str
    ) -> Optional[dict]:
        valid_statuses = ['yet_to_start', 'in_progress', 'completed']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        return question_store.update_question_progress(
            question_subtopics_id=question_subtopics_id,
            status=status
        )

    def delete_question_progress(self, question_subtopics_id: int) -> bool:
        return question_store.delete_question_progress(question_subtopics_id)

    def get_question_subtopics_with_progress(self, question_id: int) -> List[dict]:
        return question_store.get_question_subtopics_with_progress(question_id)


question_subtopic_service = QuestionSubtopicService()

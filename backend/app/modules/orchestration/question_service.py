from typing import List, Optional
from uuid import UUID
from app.modules.persistence.question_store import question_store
from app.modules.orchestration.question_subtopic_service import question_subtopic_service


class QuestionService:
    def create_question_assignment(
        self,
        question_name: str,
        curriculum_book_name: str,
        student_username: str,
        assigned_by_username: str,
        exam_id: str
    ) -> dict:
        if not question_name or not question_name.strip():
            raise ValueError("Question name cannot be empty")
        if not student_username or not student_username.strip():
            raise ValueError("Student username cannot be empty")
        
        return question_store.create_question_assignment(
            question_name=question_name,
            curriculum_book_name=curriculum_book_name,
            student_username=student_username,
            assigned_by_username=assigned_by_username,
            exam_id=exam_id
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

    def get_question_assignments_by_exam_id(
        self,
        exam_id: str,
        student_username: Optional[str] = None,
        assigned_by_username: Optional[str] = None
    ) -> List[dict]:
        return question_store.get_question_assignments_by_exam_id(
            exam_id=exam_id,
            student_username=student_username,
            assigned_by_username=assigned_by_username
        )

    def get_questions_progress(
        self,
        student_username: str,
        curriculum_book_name: str
    ) -> List[dict]:
        if not student_username or not student_username.strip():
            raise ValueError("Student username cannot be empty")
        if not curriculum_book_name or not str(curriculum_book_name).strip():
            raise ValueError("Curriculum book name cannot be empty")

        return question_store.get_questions_progress(
            student_username=student_username,
            curriculum_book_name=curriculum_book_name
        )

    def get_questions_numeric_progress(
        self,
        exam_id: UUID,
        student_username: str,
        question_names: List[str],
    ) -> List[dict]:
        if not student_username or not student_username.strip():
            raise ValueError("Student username cannot be empty")
        if not question_names:
            return []

        exam_id_str = str(exam_id)
        results: List[dict] = []

        for raw_name in question_names:
            question_name = (raw_name or "").strip()
            if not question_name:
                results.append(
                    {
                        "question_name": raw_name,
                        "question_id": None,
                        "total_subtopics": 0,
                        "completed_subtopics": 0,
                        "progress_ratio": 0.0,
                    }
                )
                continue

            assignment = question_store.get_question_assignment_by_exam_student_name(
                exam_id=exam_id_str,
                student_username=student_username,
                question_name=question_name,
            )
            if not assignment:
                results.append(
                    {
                        "question_name": question_name,
                        "question_id": None,
                        "total_subtopics": 0,
                        "completed_subtopics": 0,
                        "progress_ratio": 0.0,
                    }
                )
                continue

            question_id = int(assignment["question_id"])
            counts = question_store.get_question_subtopics_progress_counts(
                question_id=question_id,
                student_username=student_username,
            )
            total_subtopics = int(counts.get("total_subtopics") or 0)
            completed_subtopics = int(counts.get("completed_subtopics") or 0)
            progress_ratio = (completed_subtopics / total_subtopics) if total_subtopics > 0 else 0.0

            results.append(
                {
                    "question_name": question_name,
                    "question_id": question_id,
                    "total_subtopics": total_subtopics,
                    "completed_subtopics": completed_subtopics,
                    "progress_ratio": float(progress_ratio),
                }
            )

        return results

    def get_question_assignment_with_subtopics(self, question_id: int) -> Optional[dict]:
        assignment = question_store.get_question_assignment(question_id)
        if not assignment:
            return None
        subtopics_with_progress = question_subtopic_service.get_question_subtopics_with_progress(question_id)
        return {
            **assignment,
            "subtopics": subtopics_with_progress
        }

    def update_question_assignment(
        self,
        question_id: int,
        question_name: Optional[str] = None,
        curriculum_book_name: Optional[str] = None,
        student_username: Optional[str] = None,
        exam_id: Optional[str] = None
    ) -> Optional[dict]:
        if question_name and not question_name.strip():
            raise ValueError("Question name cannot be empty")
        if student_username and not student_username.strip():
            raise ValueError("Student username cannot be empty")
        
        return question_store.update_question_assignment(
            question_id=question_id,
            question_name=question_name,
            curriculum_book_name=curriculum_book_name,
            student_username=student_username,
            exam_id=exam_id
        )

    def delete_question_assignment(self, question_id: int) -> bool:
        return question_store.delete_question_assignment(question_id)

    def create_question_subtopic(
        self,
        question_id: int,
        subtopic_name: str
    ) -> dict:
        return question_subtopic_service.create_question_subtopic(
            question_id=question_id,
            subtopic_name=subtopic_name
        )

    def get_question_subtopics(
        self,
        question_id: int
    ) -> List[dict]:
        return question_subtopic_service.get_question_subtopics(question_id)

    def delete_question_subtopic(
        self,
        question_subtopics_id: int
    ) -> bool:
        return question_subtopic_service.delete_question_subtopic(question_subtopics_id)

    def get_question_progress(
        self,
        question_subtopics_id: int
    ) -> Optional[dict]:
        return question_subtopic_service.get_question_progress(question_subtopics_id)

    def update_question_progress(
        self,
        question_subtopics_id: int,
        status: str
    ) -> Optional[dict]:
        return question_subtopic_service.update_question_progress(
            question_subtopics_id=question_subtopics_id,
            status=status
        )


question_service = QuestionService()

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
from app.schemas.question import (
    QuestionAssignmentCreate,
    QuestionAssignmentRead,
    QuestionAssignmentWithSubtopics,
    QuestionSubtopicCreate,
    QuestionSubtopicRead,
    QuestionProgressRead,
    QuestionProgressUpdate
)
from app.services.question_service import question_service
from app.services.question_subtopic_service import question_subtopic_service
from app.core.security import get_current_username

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/assignments", response_model=QuestionAssignmentRead)
async def create_question_assignment(
    assignment_data: QuestionAssignmentCreate,
    username: str = Depends(get_current_username)
):
    try:
        assignment = question_service.create_question_assignment(
            question_name=assignment_data.question_name,
            curriculum_book_name=assignment_data.curriculum_book_name,
            student_username=assignment_data.student_username,
            assigned_by_username=username,
            exam_id=str(assignment_data.exam_id)
        )
        logger.info(f"Created question assignment: {assignment}")
        return assignment
    except ValueError as e:
        logger.warning(f"Error creating question assignment: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments", response_model=List[QuestionAssignmentRead])
async def list_question_assignments(
    student_username: Optional[str] = Query(None),
    username: str = Depends(get_current_username)
):
    try:
        assignments = question_service.get_question_assignments(
            student_username=student_username,
            assigned_by_username=None if student_username else username
        )
        logger.info(f"List question assignments: {assignments}")
        return assignments
    except Exception as e:
        logger.error(f"Error listing question assignments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments/exam/{exam_id}", response_model=List[QuestionAssignmentRead])
async def list_question_assignments_by_exam(
    exam_id: UUID,
    student_username: str = Query(...),  # 👈 comes from ?student_username=
    username: str = Depends(get_current_username)
):
    try:
        assignments = question_service.get_question_assignments_by_exam_id(
            str(exam_id),
            student_username=student_username,
            assigned_by_username=username
        )
        logger.info(f"List question assignments for exam {exam_id}: {assignments}")
        return assignments
    except Exception as e:
        logger.error(f"Error listing question assignments for exam: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assignments/{question_id}", response_model=QuestionAssignmentWithSubtopics)
async def get_question_assignment(
    question_id: int,
    username: str = Depends(get_current_username)
):
    try:
        assignment = question_service.get_question_assignment_with_subtopics(question_id)
        logger.info(f"Get question assignment {question_id}: {assignment}")
        if not assignment:
            raise HTTPException(status_code=404, detail="Question assignment not found")
        return assignment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting question assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/assignments/{question_id}")
async def delete_question_assignment(
    question_id: int,
    username: str = Depends(get_current_username)
):
    success = question_service.delete_question_assignment(question_id)
    response = {"status": "success", "message": "Question assignment deleted"}
    logger.info(f"Delete question assignment {question_id} result: {success}")
    if not success:
        raise HTTPException(status_code=404, detail="Question assignment not found")
    return response


@router.post("/subtopics", response_model=QuestionSubtopicRead)
async def create_question_subtopic(
    subtopic_data: QuestionSubtopicCreate,
    username: str = Depends(get_current_username)
):
    try:
        subtopic = question_service.create_question_subtopic(
            question_id=subtopic_data.question_id,
            subtopic_name=subtopic_data.subtopic_name
        )
        logger.info(f"Created question subtopic: {subtopic}")
        return subtopic
    except ValueError as e:
        logger.warning(f"Error creating question subtopic: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assignments/{question_id}/subtopics", response_model=List[QuestionSubtopicRead])
async def list_question_subtopics(
    question_id: int,
    username: str = Depends(get_current_username)
):
    try:
        subtopics = question_service.get_question_subtopics(question_id)
        logger.info(f"List question subtopics for {question_id}: {subtopics}")
        return subtopics
    except Exception as e:
        logger.error(f"Error listing question subtopics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/subtopics/{question_subtopics_id}")
async def delete_question_subtopic(
    question_subtopics_id: int,
    username: str = Depends(get_current_username)
):
    success = question_service.delete_question_subtopic(question_subtopics_id)
    response = {"status": "success", "message": "Question subtopic deleted"}
    logger.info(f"Delete question subtopic {question_subtopics_id} result: {success}")
    if not success:
        raise HTTPException(status_code=404, detail="Question subtopic not found")
    return response


@router.get("/subtopics/{question_subtopics_id}/progress", response_model=QuestionProgressRead)
async def get_question_progress(
    question_subtopics_id: int,
    username: str = Depends(get_current_username)
):
    progress = question_service.get_question_progress(question_subtopics_id)
    logger.info(f"Get question progress for {question_subtopics_id}: {progress}")
    if not progress:
        raise HTTPException(status_code=404, detail="Question progress not found")
    return progress


@router.put("/subtopics/{question_subtopics_id}/progress", response_model=QuestionProgressRead)
async def update_question_progress(
    question_subtopics_id: int,
    progress_data: QuestionProgressUpdate,
    username: str = Depends(get_current_username)
):
    try:
        progress = question_service.update_question_progress(
            question_subtopics_id=question_subtopics_id,
            status=progress_data.status
        )
        logger.info(f"Updated question progress for {question_subtopics_id}: {progress}")
        if not progress:
            raise HTTPException(status_code=404, detail="Question progress not found")
        return progress
    except ValueError as e:
        logger.warning(f"Error updating question progress: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

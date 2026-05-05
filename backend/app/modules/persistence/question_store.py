from typing import List, Optional
from psycopg2.extras import RealDictCursor
from app.db.session import db_session


class QuestionStore:
    def create_question_assignment(
        self,
        question_name: str,
        curriculum_book_name: str,
        student_username: str,
        assigned_by_username: str,
        exam_id: str
    ) -> dict:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO question_assignments 
                    (question_name, curriculum_book_name, student_username, assigned_by_username, exam_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING question_id, question_name, curriculum_book_name, 
                              student_username, assigned_by_username, assigned_at, exam_id
                    """,
                    (question_name, curriculum_book_name, student_username, assigned_by_username, exam_id)
                )
                question = cur.fetchone()
                conn.commit()
                return dict(question)

    def get_question_assignments(
        self,
        student_username: Optional[str] = None,
        assigned_by_username: Optional[str] = None
    ) -> List[dict]:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT question_id, question_name, curriculum_book_name, 
                           student_username, assigned_by_username, assigned_at, exam_id
                    FROM question_assignments
                    WHERE 1=1
                """
                params = []
                
                if student_username:
                    query += " AND student_username = %s"
                    params.append(student_username)
                    
                if assigned_by_username:
                    query += " AND assigned_by_username = %s"
                    params.append(assigned_by_username)
                    
                query += " ORDER BY assigned_at DESC"
                
                cur.execute(query, tuple(params))
                questions = cur.fetchall()
                return [dict(q) for q in questions]

    def get_question_assignment(self, question_id: int) -> Optional[dict]:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT question_id, question_name, curriculum_book_name, 
                           student_username, assigned_by_username, assigned_at, exam_id
                    FROM question_assignments
                    WHERE question_id = %s
                    """,
                    (question_id,)
                )
                question = cur.fetchone()
                return dict(question) if question else None

    def get_question_assignments_by_exam_id(
        self,
        exam_id: str,
        student_username: Optional[str] = None,
        assigned_by_username: Optional[str] = None
    ) -> List[dict]:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT question_id, question_name, curriculum_book_name, 
                           student_username, assigned_by_username, assigned_at, exam_id
                    FROM question_assignments
                    WHERE exam_id = %s
                """
                params = [exam_id]
                
                if student_username:
                    query += " AND student_username = %s"
                    params.append(student_username)
                    
                if assigned_by_username:
                    query += " AND assigned_by_username = %s"
                    params.append(assigned_by_username)
                    
                query += " ORDER BY assigned_at DESC"
                
                cur.execute(query, tuple(params))
                questions = cur.fetchall()
                return [dict(q) for q in questions]

    def update_question_assignment(
        self,
        question_id: int,
        question_name: Optional[str] = None,
        curriculum_book_name: Optional[str] = None,
        student_username: Optional[str] = None,
        exam_id: Optional[str] = None
    ) -> Optional[dict]:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                updates = []
                params = []
                
                if question_name:
                    updates.append("question_name = %s")
                    params.append(question_name)
                    
                if curriculum_book_name:
                    updates.append("curriculum_book_name = %s")
                    params.append(curriculum_book_name)
                    
                if student_username:
                    updates.append("student_username = %s")
                    params.append(student_username)
                
                if exam_id:
                    updates.append("exam_id = %s")
                    params.append(exam_id)
                
                if not updates:
                    return self.get_question_assignment(question_id)
                
                params.append(question_id)
                
                query = f"""
                    UPDATE question_assignments
                    SET {', '.join(updates)}
                    WHERE question_id = %s
                    RETURNING question_id, question_name, curriculum_book_name, 
                              student_username, assigned_by_username, assigned_at, exam_id
                """
                
                cur.execute(query, tuple(params))
                question = cur.fetchone()
                conn.commit()
                return dict(question) if question else None

    def delete_question_assignment(self, question_id: int) -> bool:
        with db_session.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM question_assignments WHERE question_id = %s",
                    (question_id,)
                )
                deleted = cur.rowcount > 0
                conn.commit()
                return deleted

    def create_question_subtopic(
        self,
        question_id: int,
        subtopic_name: str
    ) -> dict:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO question_subtopics (question_id, subtopic_name)
                    VALUES (%s, %s)
                    RETURNING question_subtopics_id, question_id, subtopic_name
                    """,
                    (question_id, subtopic_name)
                )
                subtopic = cur.fetchone()
                
                question_assignment = self.get_question_assignment(question_id)
                if question_assignment:
                    cur.execute(
                        """
                        INSERT INTO question_progress (question_subtopics_id, student_username, status)
                        VALUES (%s, %s, 'yet_to_start')
                        RETURNING question_subtopics_id, student_username, status, updated_at
                        """,
                        (subtopic['question_subtopics_id'], question_assignment['student_username'])
                    )
                
                conn.commit()
                return dict(subtopic)

    def create_question_subtopics_and_progress(
        self,
        question_id: int,
        subtopic_names: List[str],
        default_status: str = "in_progress",
    ) -> List[dict]:
        question_assignment = self.get_question_assignment(question_id)
        if not question_assignment:
            raise ValueError(f"Question assignment with id {question_id} not found")

        valid_statuses = ["yet_to_start", "in_progress", "completed"]
        if default_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        student_username = question_assignment["student_username"]
        created_or_existing: List[dict] = []

        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for raw_name in subtopic_names:
                    subtopic_name = (raw_name or "").strip()
                    if not subtopic_name:
                        continue

                    cur.execute(
                        """
                        INSERT INTO question_subtopics (question_id, subtopic_name)
                        VALUES (%s, %s)
                        ON CONFLICT (question_id, subtopic_name) DO NOTHING
                        RETURNING question_subtopics_id, question_id, subtopic_name
                        """,
                        (question_id, subtopic_name),
                    )
                    subtopic = cur.fetchone()
                    if not subtopic:
                        cur.execute(
                            """
                            SELECT question_subtopics_id, question_id, subtopic_name
                            FROM question_subtopics
                            WHERE question_id = %s AND subtopic_name = %s
                            """,
                            (question_id, subtopic_name),
                        )
                        subtopic = cur.fetchone()

                    if not subtopic:
                        continue

                    cur.execute(
                        """
                        INSERT INTO question_progress (question_subtopics_id, student_username, status)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (question_subtopics_id) DO NOTHING
                        """,
                        (subtopic["question_subtopics_id"], student_username, default_status),
                    )
                    created_or_existing.append(dict(subtopic))

                conn.commit()

        return created_or_existing

    def get_question_subtopics(self, question_id: int) -> List[dict]:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT question_subtopics_id, question_id, subtopic_name
                    FROM question_subtopics
                    WHERE question_id = %s
                    ORDER BY question_subtopics_id
                    """,
                    (question_id,)
                )
                subtopics = cur.fetchall()
                return [dict(s) for s in subtopics]

    def get_question_subtopic(self, question_subtopics_id: int) -> Optional[dict]:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT question_subtopics_id, question_id, subtopic_name
                    FROM question_subtopics
                    WHERE question_subtopics_id = %s
                    """,
                    (question_subtopics_id,)
                )
                subtopic = cur.fetchone()
                return dict(subtopic) if subtopic else None

    def update_question_subtopic(
        self,
        question_subtopics_id: int,
        subtopic_name: Optional[str] = None
    ) -> Optional[dict]:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                updates = []
                params = []
                
                if subtopic_name:
                    updates.append("subtopic_name = %s")
                    params.append(subtopic_name)
                
                if not updates:
                    return self.get_question_subtopic(question_subtopics_id)
                
                params.append(question_subtopics_id)
                
                query = f"""
                    UPDATE question_subtopics
                    SET {', '.join(updates)}
                    WHERE question_subtopics_id = %s
                    RETURNING question_subtopics_id, question_id, subtopic_name
                """
                
                cur.execute(query, tuple(params))
                subtopic = cur.fetchone()
                conn.commit()
                return dict(subtopic) if subtopic else None

    def delete_question_subtopic(self, question_subtopics_id: int) -> bool:
        with db_session.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM question_subtopics WHERE question_subtopics_id = %s",
                    (question_subtopics_id,)
                )
                deleted = cur.rowcount > 0
                conn.commit()
                return deleted

    def create_question_progress(
        self,
        question_subtopics_id: int,
        student_username: str,
        status: str = 'yet_to_start'
    ) -> dict:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO question_progress (question_subtopics_id, student_username, status)
                    VALUES (%s, %s, %s)
                    RETURNING question_subtopics_id, student_username, status, updated_at
                    """,
                    (question_subtopics_id, student_username, status)
                )
                progress = cur.fetchone()
                conn.commit()
                return dict(progress)

    def get_all_question_progress(self) -> List[dict]:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT question_subtopics_id, student_username, status, updated_at
                    FROM question_progress
                    """
                )
                progress = cur.fetchall()
                return [dict(p) for p in progress]

    def delete_question_progress(self, question_subtopics_id: int) -> bool:
        with db_session.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM question_progress WHERE question_subtopics_id = %s",
                    (question_subtopics_id,)
                )
                deleted = cur.rowcount > 0
                conn.commit()
                return deleted

    def get_question_progress(self, question_subtopics_id: int) -> Optional[dict]:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT question_subtopics_id, student_username, status, updated_at
                    FROM question_progress
                    WHERE question_subtopics_id = %s
                    """,
                    (question_subtopics_id,)
                )
                progress = cur.fetchone()
                return dict(progress) if progress else None

    def update_question_progress(
        self,
        question_subtopics_id: int,
        status: str
    ) -> Optional[dict]:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    UPDATE question_progress
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE question_subtopics_id = %s
                    RETURNING question_subtopics_id, student_username, status, updated_at
                    """,
                    (status, question_subtopics_id)
                )
                progress = cur.fetchone()
                conn.commit()
                return dict(progress) if progress else None

    def get_question_subtopics_with_progress(self, question_id: int) -> List[dict]:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT 
                        qs.question_subtopics_id,
                        qs.question_id,
                        qs.subtopic_name,
                        qp.student_username,
                        qp.status,
                        qp.updated_at
                    FROM question_subtopics qs
                    LEFT JOIN question_progress qp 
                        ON qs.question_subtopics_id = qp.question_subtopics_id
                    WHERE qs.question_id = %s
                    ORDER BY qs.question_subtopics_id
                    """,
                    (question_id,)
                )
                results = cur.fetchall()
                return [dict(r) for r in results]

    def get_questions_progress(
        self,
        student_username: str,
        curriculum_book_name: str
    ) -> List[dict]:
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        qa.question_id,
                        CASE
                            WHEN qs.question_subtopics_id IS NULL THEN qa.question_name
                            ELSE qa.question_name || ':' || qs.subtopic_name
                        END AS question_name,
                        CASE
                            WHEN qs.question_subtopics_id IS NULL THEN 'TODO'
                            ELSE CASE COALESCE(qp.status, 'yet_to_start')
                                WHEN 'completed' THEN 'completed'
                                WHEN 'in_progress' THEN 'InProgress'
                                ELSE 'TODO'
                            END
                        END AS status
                    FROM question_assignments qa
                    LEFT JOIN question_subtopics qs
                        ON qs.question_id = qa.question_id
                    LEFT JOIN question_progress qp
                        ON qp.question_subtopics_id = qs.question_subtopics_id
                        AND qp.student_username = qa.student_username
                    WHERE qa.student_username = %s
                      AND qa.curriculum_book_name = %s
                    ORDER BY qa.question_id, qs.question_subtopics_id NULLS FIRST
                    """,
                    (student_username, curriculum_book_name)
                )
                rows = cur.fetchall()
                return [dict(r) for r in rows]


question_store = QuestionStore()

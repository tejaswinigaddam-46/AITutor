from typing import List, Optional, Tuple
from uuid import UUID
from psycopg2.extras import RealDictCursor
from app.db.session import db_session

MAX_CONVERSATIONS_PER_USER = 50


class ConversationStore:
    def create_message(
        self,
        username: str,
        conversation_id: UUID,
        role: str,
        content: str,
        curriculum_book_name: str,
        summary: Optional[str] = None,
        title: Optional[str] = None
    ) -> Tuple[dict, bool]:
        """
        Creates a new message. If conversation_id is None or doesn't exist for user,
        creates a new conversation first.

        Returns: (message_dict, is_new_conversation)
        """
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                is_new_conversation = False

                cur.execute(
                    """
                    SELECT id FROM conversations
                    WHERE id = %s AND username = %s
                    """,
                    (str(conversation_id), username)
                )
                existing_convo = cur.fetchone()

                if not existing_convo:
                    cur.execute(
                        """
                        SELECT COUNT(*) as count FROM conversations WHERE username = %s
                        """,
                        (username,)
                    )
                    count_result = cur.fetchone()
                    convo_count = count_result['count']

                    if convo_count >= MAX_CONVERSATIONS_PER_USER:
                        cur.execute(
                            """
                            SELECT id FROM conversations
                            WHERE username = %s
                            ORDER BY created_at ASC
                            LIMIT 1
                            """,
                            (username,)
                        )
                        oldest = cur.fetchone()
                        if oldest:
                            cur.execute(
                                "DELETE FROM conversations WHERE id = %s",
                                (oldest['id'],)
                            )

                    cur.execute(
                        """
                        INSERT INTO conversations (id, username, curriculum_book_name, title)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id, username, curriculum_book_name, title, created_at, updated_at
                        """,
                        (str(conversation_id), username, curriculum_book_name, title)
                    )
                    new_convo = cur.fetchone()
                    is_new_conversation = True

                cur.execute(
                    """
                    INSERT INTO messages (conversation_id, role, content, summary)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, conversation_id, role, content, summary, created_at
                    """,
                    (str(conversation_id), role, content, summary)
                )
                message = cur.fetchone()

                conn.commit()
                print(f"DEBUG: {role} message saved to db with summary: {summary}")
                return dict(message), is_new_conversation

    def get_conversations(self, username: str, limit: int = 50) -> List[dict]:
        """Get all conversations for a user, ordered by most recent."""
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, username, curriculum_book_name, title, created_at, updated_at
                    FROM conversations
                    WHERE username = %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                    """,
                    (username, limit)
                )
                conversations = cur.fetchall()
                return [dict(c) for c in conversations]

    def get_conversation(self, conversation_id: UUID, username: str) -> Optional[dict]:
        """Get a specific conversation if it belongs to the user."""
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, username, curriculum_book_name, title, created_at, updated_at
                    FROM conversations
                    WHERE id = %s AND username = %s
                    """,
                    (str(conversation_id), username)
                )
                conversation = cur.fetchone()
                return dict(conversation) if conversation else None

    def get_messages(self, conversation_id: UUID, username: str) -> List[dict]:
        """Get all messages for a conversation, ensuring user owns the conversation."""
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT m.id, m.conversation_id, m.role, m.content, m.summary, m.created_at
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE m.conversation_id = %s AND c.username = %s
                    ORDER BY m.created_at ASC
                    """,
                    (str(conversation_id), username)
                )
                messages = cur.fetchall()
                return [dict(m) for m in messages]

    def delete_conversation(self, conversation_id: UUID, username: str) -> bool:
        """
        Delete a conversation and all its messages (CASCADE).
        Returns True if deleted, False if not found or not owned by user.
        """
        with db_session.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM conversations
                    WHERE id = %s AND username = %s
                    """,
                    (str(conversation_id), username)
                )
                deleted = cur.rowcount > 0
                conn.commit()
                return deleted

    def delete_message(self, message_id: UUID, username: str) -> bool:
        """
        Delete a specific message, verifying user owns the conversation.
        Returns True if deleted, False if not found or not authorized.
        """
        with db_session.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM messages m
                    USING conversations c
                    WHERE m.id = %s
                    AND m.conversation_id = c.id
                    AND c.username = %s
                    """,
                    (str(message_id), username)
                )
                deleted = cur.rowcount > 0
                conn.commit()
                return deleted

    def update_message_summary(self, message_id: UUID, username: str, summary: str) -> bool:
        """
        Update the summary of a specific message, verifying user owns the conversation.
        Returns True if updated, False if not found or not authorized.
        """
        with db_session.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE messages m
                    SET summary = %s
                    FROM conversations c
                    WHERE m.id = %s
                    AND m.conversation_id = c.id
                    AND c.username = %s
                    """,
                    (summary, str(message_id), username)
                )
                updated = cur.rowcount > 0
                conn.commit()
                return updated

    def update_api_count(self):
        try:
            with db_session.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE countapihit SET count = count + 1
                        """,
                    )
                    conn.commit()
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error updating API count: {e}")


conversation_store = ConversationStore()

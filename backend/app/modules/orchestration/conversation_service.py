from typing import List, Optional, Tuple
from uuid import UUID, uuid4
from app.modules.persistence.conversation_store import conversation_store


class ConversationService:
    async def create_message(
        self,
        username: str,
        conversation_id: Optional[UUID],
        role: str,
        content: str,
        curriculum_book_name: str,
        summary: Optional[str] = None,
        title: Optional[str] = None,
        question_id: Optional[int] = None,
        question_subtopics_id: Optional[int] = None,
    ) -> Tuple[dict, bool]:
        """
        Business logic for creating a message.
        Validates content and delegates DB operations to conversation_store.
        """
        # Validation: Ensure content is not empty
        if not content or not content.strip():
            raise ValueError("Message content cannot be empty")

        # Validation: Ensure role is valid (redundant with Enum but good for service layer)
        if role not in ["user", "assistant"]:
            raise ValueError("Invalid message role")

        # If no conversation_id is provided, generate one
        if not conversation_id:
            conversation_id = uuid4()

        # Delegate to store
        return conversation_store.create_message(
            username=username,
            conversation_id=conversation_id,
            role=role,
            content=content,
            curriculum_book_name=curriculum_book_name,
            summary=summary,
            title=title,
            question_id=question_id,
            question_subtopics_id=question_subtopics_id,
        )

    def update_message_summary(self, message_id: UUID, username: str, summary: str) -> bool:
        """Update the summary of a specific message."""
        return conversation_store.update_message_summary(message_id, username, summary)

    def get_conversations(self, username: str, limit: int = 50) -> List[dict]:
        """Get all conversations for a user."""
        return conversation_store.get_conversations(username, limit)

    def get_conversation(self, conversation_id: UUID, username: str) -> Optional[dict]:
        """Get a specific conversation."""
        return conversation_store.get_conversation(conversation_id, username)

    def get_conversation_by_question(self, username: str, question_id: int) -> Optional[dict]:
        return conversation_store.get_conversation_by_question(username=username, question_id=question_id)

    def get_conversation_by_question_subtopic(
        self,
        username: str,
        question_subtopics_id: int,
    ) -> Optional[dict]:
        return conversation_store.get_conversation_by_question_subtopic(
            username=username,
            question_subtopics_id=question_subtopics_id,
        )

    def create_feedback_overview_interaction(
        self,
        username: str,
        conversation_id: Optional[UUID],
        curriculum_book_name: str,
        user_content: str,
        user_title: Optional[str],
        assistant_content: str,
        assistant_title: Optional[str],
        question_id: Optional[int],
        question_subtopics_id: Optional[int],
        subtopic_names: List[str],
    ) -> Tuple[UUID, dict, dict, bool]:
        if not conversation_id:
            conversation_id = uuid4()

        user_message, assistant_message, is_new = conversation_store.create_feedback_overview_interaction(
            username=username,
            conversation_id=conversation_id,
            curriculum_book_name=curriculum_book_name,
            user_content=user_content,
            user_title=user_title,
            assistant_content=assistant_content,
            assistant_title=assistant_title,
            question_id=question_id,
            question_subtopics_id=question_subtopics_id,
            subtopic_names=subtopic_names,
        )
        return conversation_id, user_message, assistant_message, is_new

    def get_messages(self, conversation_id: UUID, username: str) -> List[dict]:
        """Get all messages for a conversation."""
        return conversation_store.get_messages(conversation_id, username)

    def delete_conversation(self, conversation_id: UUID, username: str) -> bool:
        """Delete a conversation."""
        return conversation_store.delete_conversation(conversation_id, username)

    def delete_message(self, message_id: UUID, username: str) -> bool:
        """Delete a specific message."""
        return conversation_store.delete_message(message_id, username)


conversation_service = ConversationService()

from typing import List, Optional, Tuple
from uuid import UUID, uuid4
from app.db.conversation_store import conversation_store


class ConversationService:
    def create_message(
        self,
        username: str,
        conversation_id: Optional[UUID],
        role: str,
        content: str,
        curriculum_book_name: str,
        title: Optional[str] = None
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
            title=title
        )

    def get_conversations(self, username: str, limit: int = 50) -> List[dict]:
        """Get all conversations for a user."""
        return conversation_store.get_conversations(username, limit)

    def get_conversation(self, conversation_id: UUID, username: str) -> Optional[dict]:
        """Get a specific conversation."""
        return conversation_store.get_conversation(conversation_id, username)

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

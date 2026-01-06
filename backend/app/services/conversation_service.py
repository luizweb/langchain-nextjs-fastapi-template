"""Service for conversation management."""

from datetime import datetime
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation


class ConversationService:
    """Service for managing conversations."""

    @staticmethod
    async def create_conversation(
        project_id: int,
        session: AsyncSession,
        title: str = 'Novo chat'
    ) -> Conversation:
        """Create a new conversation.

        Args:
            project_id: The project ID
            session: Database session
            title: Conversation title (default: 'New Conversation')

        Returns:
            The created Conversation instance
        """
        conversation = Conversation(project_id=project_id, title=title)
        session.add(conversation)
        await session.flush()
        await session.refresh(conversation)
        return conversation

    @staticmethod
    async def get_conversation(
        conversation_id: int,
        session: AsyncSession
    ) -> Conversation | None:
        """Get conversation by ID.

        Args:
            conversation_id: The conversation ID
            session: Database session

        Returns:
            Conversation instance or None if not found
        """
        return await session.scalar(
            select(Conversation).where(Conversation.id == conversation_id)
        )

    @staticmethod
    async def list_conversations(
        project_id: int,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[Conversation]:
        """List conversations for project.

        Args:
            project_id: The project ID
            session: Database session
            limit: Maximum results (default: 50)
            offset: Results to skip (default: 0)

        Returns:
            List of Conversation instances ordered by updated_at desc
        """
        result = await session.scalars(
            select(Conversation)
            .where(Conversation.project_id == project_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.all()

    @staticmethod
    async def update_conversation_title(
        conversation_id: int,
        title: str,
        session: AsyncSession
    ) -> Conversation | None:
        """Update conversation title.

        Args:
            conversation_id: The conversation ID
            title: New title
            session: Database session

        Returns:
            Updated Conversation instance or None if not found
        """
        conversation = await session.scalar(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.now()
            await session.flush()
            await session.refresh(conversation)
        return conversation

    @staticmethod
    async def delete_conversation(
        conversation_id: int,
        session: AsyncSession
    ) -> bool:
        """Delete conversation.

        Args:
            conversation_id: The conversation ID
            session: Database session

        Returns:
            True if deleted, False if not found
        """
        result = await session.execute(
            delete(Conversation).where(Conversation.id == conversation_id)
        )
        return result.rowcount > 0

    @staticmethod
    def get_thread_id(conversation_id: int) -> str:
        """Generate thread_id from conversation_id.

        Args:
            conversation_id: The conversation ID

        Returns:
            Thread ID in format 'conversation_{id}'
        """
        return f'conversation_{conversation_id}'

    @staticmethod
    async def generate_title_from_message(message: str) -> str:
        """Generate title from first message (max 50 chars).

        Args:
            message: The user's first message

        Returns:
            A truncated title
        """
        title = message.strip()
        if len(title) > 50:
            title = title[:47] + '...'
        return title if title else 'New Conversation'

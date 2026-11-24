from typing import List, Optional, Any, Dict
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, Message


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_conversation(self, title: str = "New Conversation") -> Conversation:
        conv = Conversation(title=title)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def list_conversations(self, skip: int = 0, limit: int = 50) -> List[Conversation]:
        return (
            self.db.query(Conversation)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_conversations(self) -> int:
        return self.db.query(Conversation).count()

    def count_messages(self) -> int:
        return self.db.query(Message).count()

    def delete_conversation(self, conversation_id: str) -> bool:
        conv = self.get_conversation(conversation_id)
        if not conv:
            return False
        self.db.delete(conv)
        self.db.commit()
        return True

    def create_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations or [],
            retrieved_chunks=retrieved_chunks or []
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_messages(self, conversation_id: str) -> List[Message]:
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )


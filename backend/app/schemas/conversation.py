from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.rag import Citation
from app.schemas.chunk import ChunkSearchHit


class MessageRead(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    citations: List[Citation] = Field(default_factory=list)
    retrieved_chunks: List[ChunkSearchHit] = Field(default_factory=list)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"


class ConversationRead(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(ConversationRead):
    messages: List[MessageRead] = Field(default_factory=list)

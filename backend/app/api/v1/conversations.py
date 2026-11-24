from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.conversation import ConversationRead, ConversationDetail
from app.repositories.conversation_repo import ConversationRepository

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("", response_model=APIResponse[List[ConversationRead]])
def list_conversations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists conversation history threads."""
    repo = ConversationRepository(db)
    convs = repo.list_conversations(skip=skip, limit=limit)
    return APIResponse(
        success=True,
        message=f"Retrieved {len(convs)} conversation threads.",
        data=[ConversationRead.model_validate(c) for c in convs]
    )


@router.get("/{conversation_id}", response_model=APIResponse[ConversationDetail])
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves conversation thread with all grounded messages and citations."""
    repo = ConversationRepository(db)
    conv = repo.get_conversation(conversation_id)
    if not conv:
        return APIResponse(success=False, message="Conversation not found", data=None)

    return APIResponse(
        success=True,
        message="Conversation loaded.",
        data=ConversationDetail.model_validate(conv)
    )


@router.delete("/{conversation_id}", response_model=APIResponse[bool])
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Deletes conversation thread."""
    repo = ConversationRepository(db)
    deleted = repo.delete_conversation(conversation_id)
    return APIResponse(
        success=deleted,
        message="Conversation deleted." if deleted else "Conversation not found.",
        data=deleted
    )


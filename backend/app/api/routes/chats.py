from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.collections import get_owned_collection
from app.core.database import get_db
from app.models.chat import Chat
from app.models.user import User
from app.schemas.chat import ChatDetail, ChatRename, ChatSummary

router = APIRouter(prefix="/chats", tags=["chats"])


def get_owned_chat(chat_id: int, db: Session, current_user: User) -> Chat:
    chat = db.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    get_owned_collection(chat.collection_id, db, current_user)
    return chat


@router.get("", response_model=list[ChatSummary])
def list_chats(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Chat]:
    collection = get_owned_collection(collection_id, db, current_user)
    return sorted(collection.chats, key=lambda c: c.created_at, reverse=True)


@router.get("/{chat_id}", response_model=ChatDetail)
def get_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Chat:
    return get_owned_chat(chat_id, db, current_user)


@router.patch("/{chat_id}", response_model=ChatSummary)
def rename_chat(
    chat_id: int,
    payload: ChatRename,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Chat:
    chat = get_owned_chat(chat_id, db, current_user)
    chat.title = payload.title
    db.commit()
    db.refresh(chat)
    return chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    chat = get_owned_chat(chat_id, db, current_user)
    db.delete(chat)
    db.commit()

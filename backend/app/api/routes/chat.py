from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.api.deps import get_current_user
from app.api.routes.chats import get_owned_chat
from app.api.routes.collections import get_owned_collection
from app.core.database import get_db
from app.models.chat import Chat
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services.chat import stream_chat_response

router = APIRouter(prefix="/chat", tags=["chat"])


def _make_title(message: str) -> str:
    title = message.strip().splitlines()[0]
    return title[:60] + ("…" if len(title) > 60 else "")


@router.post("")
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    get_owned_collection(payload.collection_id, db, current_user)

    if payload.chat_id is not None:
        chat_row = get_owned_chat(payload.chat_id, db, current_user)
    else:
        chat_row = Chat(collection_id=payload.collection_id, title=_make_title(payload.message))
        db.add(chat_row)
        db.commit()
        db.refresh(chat_row)

    return StreamingResponse(
        stream_chat_response(db, chat_row.id, payload.collection_id, payload.message),
        media_type="text/event-stream",
    )

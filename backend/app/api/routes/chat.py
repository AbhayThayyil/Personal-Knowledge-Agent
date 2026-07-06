from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.api.deps import get_current_user
from app.api.routes.collections import get_owned_collection
from app.core.database import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services.chat import stream_chat_response

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    get_owned_collection(payload.collection_id, db, current_user)

    return StreamingResponse(
        stream_chat_response(payload.collection_id, payload.message),
        media_type="text/event-stream",
    )

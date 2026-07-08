from sqlalchemy.orm import Session

from app.models.message import Message


def get_recent_messages(db: Session, chat_id: int, limit: int | None = None) -> list[Message]:
    """Prior messages in this chat, oldest first, excluding the current
    in-flight question (already saved before the agent loop runs).

    Pass `limit` to bound how far back this reaches; omit it to fetch the
    entire chat history (used by the get_conversation_history tool for
    lookups beyond the automatically-included window).
    """
    query = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at.desc())

    if limit is not None:
        query = query.limit(limit + 1)

    messages = list(reversed(query.all()))
    return messages[:-1] if messages else messages

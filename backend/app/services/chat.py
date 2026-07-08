import json
from collections.abc import AsyncIterator

from sqlalchemy.orm import Session

from app.agent.loop import run_agent
from app.models.message import Message


async def stream_chat_response(
    db: Session, chat_id: int, collection_id: int, question: str
) -> AsyncIterator[str]:
    db.add(Message(chat_id=chat_id, role="user", content=question, citations=[]))
    db.commit()

    yield _sse_event({"type": "start", "chat_id": chat_id})

    answer_parts: list[str] = []
    citations: list[dict] = []

    async for event in run_agent(db, collection_id, chat_id, question):
        if event["type"] == "token":
            answer_parts.append(event["content"])
        elif event["type"] == "citations":
            citations = event["citations"]
        yield _sse_event(event)

    db.add(
        Message(
            chat_id=chat_id,
            role="assistant",
            content="".join(answer_parts),
            citations=citations,
        )
    )
    db.commit()
    yield _sse_event({"type": "done", "citations": citations})


def _sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"

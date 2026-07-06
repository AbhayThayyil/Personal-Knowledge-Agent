import json
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.message import Message
from app.services.embeddings import embed_text
from app.services.vectorstore import SearchResult, search

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about the user's documents. "
    "Answer ONLY using the provided context. If the context does not contain the "
    "answer, say you don't know rather than guessing. Be concise."
)


@dataclass
class Citation:
    filename: str
    page: int


def build_messages(question: str, chunks: list[SearchResult]) -> list[dict[str, str]]:
    context = "\n\n".join(
        f"[{i + 1}] (from {chunk.filename}, page {chunk.page})\n{chunk.text}"
        for i, chunk in enumerate(chunks)
    )
    user_content = f"Context:\n{context}\n\nQuestion: {question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def dedupe_citations(chunks: list[SearchResult]) -> list[Citation]:
    seen: set[tuple[str, int]] = set()
    citations: list[Citation] = []
    for chunk in chunks:
        key = (chunk.filename, chunk.page)
        if key not in seen:
            seen.add(key)
            citations.append(Citation(filename=chunk.filename, page=chunk.page))
    return citations


async def stream_chat_response(
    db: Session, chat_id: int, collection_id: int, question: str
) -> AsyncIterator[str]:
    db.add(Message(chat_id=chat_id, role="user", content=question, citations=[]))
    db.commit()

    yield _sse_event({"type": "start", "chat_id": chat_id})

    query_embedding = await embed_text(question)
    chunks = search(collection_id, query_embedding, top_k=settings.chat_top_k)

    if not chunks:
        answer = "I couldn't find any relevant documents to answer that."
        yield _sse_event({"type": "token", "content": answer})
        db.add(Message(chat_id=chat_id, role="assistant", content=answer, citations=[]))
        db.commit()
        yield _sse_event({"type": "done", "citations": []})
        return

    messages = build_messages(question, chunks)
    answer_parts: list[str] = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{settings.ollama_base_url}/api/chat",
            json={"model": settings.chat_model, "messages": messages, "stream": True},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    answer_parts.append(content)
                    yield _sse_event({"type": "token", "content": content})

    citations = [c.__dict__ for c in dedupe_citations(chunks)]
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

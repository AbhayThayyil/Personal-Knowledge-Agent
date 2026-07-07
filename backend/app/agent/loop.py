import json
from collections.abc import AsyncIterator

import httpx
from sqlalchemy.orm import Session

from app.agent.tools import TOOL_SCHEMAS, call_tool
from app.core.config import settings

AGENT_SYSTEM_PROMPT = (
    "You are an AI agent that answers questions about documents the user has "
    "uploaded to this collection. You must ALWAYS call the search_documents "
    "tool at least once before answering any question that could relate to "
    "the user's documents, even if you already believe you know the answer "
    "from general knowledge -- the user wants the answer grounded in THEIR "
    "specific documents, not your training data. Only skip tools for pure "
    "greetings ('hi', 'thanks') with no informational content. If the question "
    "refers back to earlier conversation instead of the documents, call "
    "get_conversation_history instead of search_documents. Cite sources as "
    "(filename, page) using only filenames and pages returned by a tool -- "
    "never invent one."
)

async def run_agent(
    db: Session, collection_id: int, chat_id: int, question: str
) -> AsyncIterator[dict]:
    messages: list[dict] = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    citations: list[dict] = []
    seen_citations: set[tuple[str, int]] = set()

    for _ in range(settings.agent_max_tool_rounds):
        response = await _chat_once(messages, use_tools=True)
        tool_calls = response.get("tool_calls") or []

        if not tool_calls:
            break

        messages.append(
            {
                "role": "assistant",
                "content": response.get("content", ""),
                "tool_calls": tool_calls,
            }
        )

        for call in tool_calls:
            name = call["function"]["name"]
            arguments = call["function"]["arguments"]
            yield {"type": "tool_call", "name": name, "arguments": arguments}

            result = await call_tool(
                name, arguments, db=db, collection_id=collection_id, chat_id=chat_id
            )

            if name == "search_documents":
                for r in result.get("results", []):
                    key = (r["filename"], r["page"])
                    if key not in seen_citations:
                        seen_citations.add(key)
                        citations.append({"filename": r["filename"], "page": r["page"]})

            yield {"type": "tool_result", "name": name}
            messages.append({"role": "tool", "content": json.dumps(result)})

    yield {"type": "citations", "citations": citations}

    # Final pass with no tools attached: guarantees a text answer, not another
    # tool call, and lets us stream it token-by-token for the UI.
    async for token in _chat_stream(messages):
        yield {"type": "token", "content": token}


async def _chat_once(messages: list[dict], use_tools: bool) -> dict:
    payload = {
        "model": settings.chat_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": settings.agent_temperature},
    }
    if use_tools:
        payload["tools"] = TOOL_SCHEMAS

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(f"{settings.ollama_base_url}/api/chat", json=payload)
        response.raise_for_status()
        return response.json()["message"]


async def _chat_stream(messages: list[dict]) -> AsyncIterator[str]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.chat_model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": settings.agent_temperature},
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content

import inspect
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.message import Message
from app.services.embeddings import embed_text
from app.services.vectorstore import get_chunks_for_document, search

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": (
                "Semantically search the documents in this collection for text "
                "relevant to a query. Returns matching passages with filename and "
                "page number. Use this to find specific information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_document",
            "description": (
                "Fetch the full text of one document by its exact filename. Use "
                "this when you need the whole document rather than a few matching "
                "snippets, e.g. to summarize it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Exact filename"},
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_collection_documents",
            "description": "List every document uploaded to this collection, with its filename and processing status.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_filename",
            "description": "Find documents in this collection whose filename contains a substring. Use this when the user refers to a document by (partial) name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename_contains": {"type": "string"},
                },
                "required": ["filename_contains"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_conversation_history",
            "description": (
                "Get the prior turns of this conversation. Call this whenever the "
                "user's message refers back to earlier conversation rather than "
                "the documents themselves -- e.g. it uses words like 'that', "
                "'it', 'the one I mentioned', 'what did I just ask', or 'earlier' "
                "without naming a specific document or topic."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


async def search_documents(db: Session, collection_id: int, chat_id: int, query: str) -> dict[str, Any]:
    embedding = await embed_text(query)
    results = search(collection_id, embedding, top_k=settings.chat_top_k)
    if not results:
        return {
            "results": [],
            "note": (
                "No relevant passages found for this query. Tell the user nothing "
                "relevant was found in their documents -- do not answer from your "
                "own general knowledge instead."
            ),
        }
    return {
        "results": [
            {"filename": r.filename, "page": r.page, "text": r.text} for r in results
        ]
    }


def retrieve_document(db: Session, collection_id: int, chat_id: int, filename: str) -> dict[str, Any]:
    document = (
        db.query(Document)
        .filter(Document.collection_id == collection_id, Document.filename == filename)
        .first()
    )
    if document is None:
        return {"error": f"No document named '{filename}' found in this collection."}

    chunks = get_chunks_for_document(document.id)
    if not chunks:
        return {"error": f"'{filename}' has no processed content yet (status: {document.status})."}

    return {"filename": filename, "text": "\n\n".join(c.text for c in chunks)}


def list_collection_documents(db: Session, collection_id: int, chat_id: int) -> dict[str, Any]:
    documents = db.query(Document).filter(Document.collection_id == collection_id).all()
    return {"documents": [{"filename": d.filename, "status": d.status} for d in documents]}


def search_by_filename(db: Session, collection_id: int, chat_id: int, filename_contains: str) -> dict[str, Any]:
    documents = (
        db.query(Document)
        .filter(
            Document.collection_id == collection_id,
            Document.filename.ilike(f"%{filename_contains}%"),
        )
        .all()
    )
    return {"documents": [{"filename": d.filename, "status": d.status} for d in documents]}


def get_conversation_history(db: Session, collection_id: int, chat_id: int) -> dict[str, Any]:
    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at).all()
    # The current in-flight question was already saved before the agent loop runs, so drop it.
    prior = messages[:-1]
    return {"history": [{"role": m.role, "content": m.content} for m in prior]}


TOOL_FUNCTIONS = {
    "search_documents": search_documents,
    "retrieve_document": retrieve_document,
    "list_collection_documents": list_collection_documents,
    "search_by_filename": search_by_filename,
    "get_conversation_history": get_conversation_history,
}


async def call_tool(
    name: str, arguments: dict[str, Any], *, db: Session, collection_id: int, chat_id: int
) -> dict[str, Any]:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"Unknown tool '{name}'"}

    if inspect.iscoroutinefunction(fn):
        return await fn(db, collection_id, chat_id, **arguments)
    return fn(db, collection_id, chat_id, **arguments)

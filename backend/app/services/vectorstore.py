from functools import lru_cache

import chromadb

from app.core.config import settings
from app.services.chunking import Chunk


@lru_cache
def get_collection():
    client = chromadb.PersistentClient(path=settings.chroma_dir)
    return client.get_or_create_collection("pka_chunks")


def add_chunks(
    document_id: int,
    collection_id: int,
    filename: str,
    chunks: list[Chunk],
    embeddings: list[list[float]],
) -> None:
    if not chunks:
        return

    get_collection().add(
        ids=[f"{document_id}-{chunk.chunk_index}" for chunk in chunks],
        embeddings=embeddings,
        documents=[chunk.text for chunk in chunks],
        metadatas=[
            {
                "document_id": document_id,
                "collection_id": collection_id,
                "filename": filename,
                "page": chunk.page,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ],
    )


def delete_document_chunks(document_id: int) -> None:
    get_collection().delete(where={"document_id": document_id})

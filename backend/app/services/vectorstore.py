from dataclasses import dataclass
from functools import lru_cache

import chromadb

from app.core.config import settings
from app.services.chunking import Chunk


@dataclass
class SearchResult:
    text: str
    filename: str
    page: int
    document_id: int


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


def search(collection_id: int, query_embedding: list[float], top_k: int) -> list[SearchResult]:
    results = get_collection().query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"collection_id": collection_id},
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    return [
        SearchResult(
            text=text,
            filename=meta["filename"],
            page=meta["page"],
            document_id=meta["document_id"],
        )
        for text, meta in zip(documents, metadatas)
    ]

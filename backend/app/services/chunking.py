from dataclasses import dataclass

from app.core.config import settings


@dataclass
class Chunk:
    text: str
    page: int
    chunk_index: int


def chunk_pages(pages: list[str]) -> list[Chunk]:
    size = settings.chunk_size
    overlap = settings.chunk_overlap
    chunks: list[Chunk] = []
    chunk_index = 0

    for page_number, page_text in enumerate(pages, start=1):
        text = page_text.strip()
        if not text:
            continue

        start = 0
        while start < len(text):
            end = start + size
            piece = text[start:end].strip()
            if piece:
                chunks.append(Chunk(text=piece, page=page_number, chunk_index=chunk_index))
                chunk_index += 1
            if end >= len(text):
                break
            start = end - overlap

    return chunks

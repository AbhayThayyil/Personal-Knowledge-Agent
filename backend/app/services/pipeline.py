import logging

from app.core.database import SessionLocal
from app.models.document import Document
from app.services import vectorstore
from app.services.chunking import chunk_pages
from app.services.embeddings import embed_text
from app.services.extraction import extract_pages

logger = logging.getLogger(__name__)


async def process_document(document_id: int) -> None:
    """Runs as a background task after upload: extract -> chunk -> embed -> store."""
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:
            return

        document.status = "processing"
        db.commit()

        try:
            pages = extract_pages(document.file_path)
            chunks = chunk_pages(pages)
            embeddings = [await embed_text(chunk.text) for chunk in chunks]

            vectorstore.add_chunks(
                document_id=document.id,
                collection_id=document.collection_id,
                filename=document.filename,
                chunks=chunks,
                embeddings=embeddings,
            )

            document.status = "ready"
        except Exception:
            logger.exception("Failed to process document %s", document_id)
            document.status = "failed"

        db.commit()
    finally:
        db.close()

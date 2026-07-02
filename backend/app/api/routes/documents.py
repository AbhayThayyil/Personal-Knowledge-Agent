from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.collections import get_owned_collection
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentOut
from app.services import storage

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    collection_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    get_owned_collection(collection_id, db, current_user)

    file_path, size_bytes = await storage.save_upload(file, collection_id)

    document = Document(
        filename=file.filename or "untitled",
        file_path=file_path,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        collection_id=collection_id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Document]:
    collection = get_owned_collection(collection_id, db, current_user)
    return collection.documents


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    get_owned_collection(document.collection_id, db, current_user)

    storage.delete_file(document.file_path)
    db.delete(document)
    db.commit()

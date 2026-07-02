from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.collection import Collection
from app.models.user import User
from app.schemas.collection import CollectionCreate, CollectionOut, CollectionUpdate
from app.services import storage

router = APIRouter(prefix="/collections", tags=["collections"])


def get_owned_collection(
    collection_id: int, db: Session, current_user: User
) -> Collection:
    collection = (
        db.query(Collection)
        .filter(Collection.id == collection_id, Collection.owner_id == current_user.id)
        .first()
    )
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )
    return collection


@router.post("", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
def create_collection(
    payload: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Collection:
    collection = Collection(name=payload.name, owner_id=current_user.id)
    db.add(collection)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a collection with this name",
        )
    db.refresh(collection)
    return collection


@router.get("", response_model=list[CollectionOut])
def list_collections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Collection]:
    return db.query(Collection).filter(Collection.owner_id == current_user.id).all()


@router.patch("/{collection_id}", response_model=CollectionOut)
def rename_collection(
    collection_id: int,
    payload: CollectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Collection:
    collection = get_owned_collection(collection_id, db, current_user)
    collection.name = payload.name
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a collection with this name",
        )
    db.refresh(collection)
    return collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    collection = get_owned_collection(collection_id, db, current_user)
    for document in collection.documents:
        storage.delete_file(document.file_path)
    db.delete(collection)
    db.commit()

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    collection_id: int
    chat_id: int | None = None
    message: str = Field(min_length=1, max_length=2000)


class ChatSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    collection_id: int
    created_at: datetime


class ChatRename(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    citations: list[dict]
    created_at: datetime


class ChatDetail(ChatSummary):
    messages: list[MessageOut]

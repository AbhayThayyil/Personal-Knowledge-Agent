from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    collection_id: int
    message: str = Field(min_length=1, max_length=2000)

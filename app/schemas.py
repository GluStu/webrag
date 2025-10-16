from pydantic import BaseModel, AnyHttpUrl
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class IngestUrlRequest(BaseModel):
    url: AnyHttpUrl

class IngestUrlResponse(BaseModel):
    ingestion_id: UUID
    status: str = "queued"

class IngestionStatusResponse(BaseModel):
    id: UUID
    url: str
    status: str
    title: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class Citation(BaseModel):
    url: str
    chunk_index: int
    score: float

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    used_llm: bool

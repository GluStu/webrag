from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db import get_db
from app.models import Ingestion, Chunk
from app.schemas import IngestUrlRequest, IngestUrlResponse, IngestionStatusResponse, QueryRequest, QueryResponse, Citation
from app.url_queue import publish_ingest_job
from app.config import settings
from app.embeddings import EmbeddingModel
from app.vectorstore import FaissStore
from app.llm import answer_with_llm

app = FastAPI(title="RAG-Websites", version="0.1.0")

_embedder: EmbeddingModel | None = None
_store: FaissStore | None = None

def get_embedder() -> EmbeddingModel:
    global _embedder
    if _embedder is None:
        _embedder = EmbeddingModel(settings.EMBEDDING_MODEL_NAME)
    return _embedder

def get_store() -> FaissStore:
    global _store
    if _store is None:
        _store = FaissStore(settings.FAISS_INDEX_PATH, settings.INDEX_LOCK_PATH)
    return _store


@app.post("/ingest-url", response_model=IngestUrlResponse, status_code=202)
def ingest_url(req: IngestUrlRequest, db: Session = Depends(get_db)):
    url = str(req.url).strip()
    ing = Ingestion(url=url, status="pending")
    db.add(ing)
    db.commit()
    db.refresh(ing)
    publish_ingest_job(str(ing.id), ing.url)
    return IngestUrlResponse(ingestion_id=ing.id, status="queued")


@app.get("/ingestions/{ingestion_id}", response_model=IngestionStatusResponse)
def get_ingestion(ingestion_id: UUID, db: Session = Depends(get_db)):
    ing: Ingestion | None = db.get(Ingestion, ingestion_id)
    if not ing:
        raise HTTPException(404, "Ingestion not found")
    return IngestionStatusResponse(
        id=ing.id,
        url=ing.url,
        status=ing.status,
        title=ing.title,
        error_message=ing.error_message,
        created_at=ing.created_at,
        updated_at=ing.updated_at,
    )

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, db: Session = Depends(get_db)):
    if not req.query.strip():
        raise HTTPException(400, "Query cannot be empty")

    embedder = get_embedder()
    store = get_store()

    qvec = embedder.encode_one(req.query)
    scores, ids = store.search(qvec, top_k=req.top_k)

    if ids.size == 0:
        return QueryResponse(answer="No indexed content yet. Ingest some URLs first.", citations=[], used_llm=False)

    # Map FAISS vector ids to chunks
    # vector_id in 'chunks' matches FAISS order index.
    chunks: List[Chunk] = (
        db.query(Chunk)
        .filter(Chunk.vector_id.in_(ids.tolist()))
        .order_by(Chunk.vector_id.asc())
        .all()
    )
    # Build id->chunk mapping
    by_vec = {c.vector_id: c for c in chunks}

    packed = []
    citations: List[Citation] = []
    for score, vid in zip(scores.tolist(), ids.tolist()):
        if vid in by_vec:
            c = by_vec[vid]
            packed.append((c.text, c.url, c.chunk_index))
            citations.append(Citation(url=c.url, chunk_index=c.chunk_index, score=float(score)))

    answer, used_llm = answer_with_llm(req.query, packed)
    return QueryResponse(answer=answer, citations=citations, used_llm=used_llm)



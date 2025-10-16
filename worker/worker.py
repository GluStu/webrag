# python -m worker.worker

import json
import sys
import traceback
from uuid import UUID

import pika
from sqlalchemy.orm import Session
from app.config import settings
from app.db import SessionLocal
from app.models import Ingestion, Chunk
from app.fetcher import fetch_url
from app.chunker import chunk_text_o200k
from app.embeddings import EmbeddingModel
from app.vectorstore import FaissStore

QUEUE_NAME = "ingest-url"

def log(*args):
    print("[worker]", *args, flush=True)

def process_job(ingestion_id: str, url: str):
    db: Session = SessionLocal()
    embedder = EmbeddingModel(settings.EMBEDDING_MODEL_NAME)
    store = FaissStore(settings.FAISS_INDEX_PATH, settings.INDEX_LOCK_PATH)

    try:
        ing: Ingestion | None = db.get(Ingestion, UUID(ingestion_id))
        if not ing:
            log("ingestion not found:", ingestion_id)
            return

        ing.status = "processing"
        db.commit()

        text, title = fetch_url(url)
        if not text or len(text.strip()) < 20:
            raise ValueError("Failed to extract enough text from URL")

        if title:
            ing.title = title
            db.commit()

        # chunk
        chunks = chunk_text_o200k(
            text, max_tokens=settings.CHUNK_TOKENS, overlap=settings.CHUNK_OVERLAP
        )
        if not chunks:
            raise ValueError("No chunks produced")

        # embed
        texts = [c[0] for c in chunks]
        vecs = embedder.encode(texts)  # L2-normalized

        # append to FAISS
        start_id, end_id = store.add(vecs)
        log(f"FAISS add: {start_id} -> {end_id} (count={end_id-start_id})")

        # persist chunk rows with vector_id mapping
        for i, (chunk_text, tok_count) in enumerate(chunks):
            vector_id = start_id + i
            row = Chunk(
                ingestion_id=ing.id,
                url=url,
                chunk_index=i,
                token_count=tok_count,
                text=chunk_text,
                vector_id=vector_id,
            )
            db.add(row)
        db.commit()

        ing.status = "completed"
        db.commit()
        log("completed ingestion:", ingestion_id)

    except Exception as e:
        db.rollback()
        try:
            ing = db.get(Ingestion, UUID(ingestion_id))
            if ing:
                ing.status = "failed"
                ing.error_message = f"{e.__class__.__name__}: {e}"
                db.commit()
        except Exception:
            pass
        log("ERROR ingesting", ingestion_id, "->", e)
        traceback.print_exc(file=sys.stdout)
    finally:
        db.close()

def main():
    params = pika.URLParameters(settings.RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        try:
            msg = json.loads(body.decode("utf-8"))
            ingestion_id = msg["ingestion_id"]
            url = msg["url"]
            log("got job:", ingestion_id, url)
            process_job(ingestion_id, url)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            log("job failure, rejecting:", e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    log("worker started; waiting for messages.")
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        log("shutdown...")
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    main()
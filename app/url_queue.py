import json
import pika
from app.config import settings

QUEUE_NAME = "ingest-url"

def publish_ingest_job(ingestion_id: str, url: str):
    params = pika.URLParameters(settings.RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    try:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        body = json.dumps({"ingestion_id": ingestion_id, "url": url})
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=body,
            properties=pika.BasicProperties(delivery_mode=2),  # persistent
        )
    finally:
        connection.close()

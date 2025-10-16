python -m scripts.init_db

uvicorn app.api:app --reload --port 8000

python -m worker.worker

http POST :8000/ingest-url url={url}

curl http://localhost:8000/ingestions/{id}

http POST http://localhost:8000/query query="{query}"
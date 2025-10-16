# python -m scripts.init_db

from app.db import engine, Base
from app.models import Ingestion, Chunk  # noqa

def main():
    Base.metadata.create_all(bind=engine)
    print("Tables created/verified")

if __name__ == "__main__":
    main()
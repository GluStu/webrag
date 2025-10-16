import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def encode(self, texts: list[str]) -> np.ndarray:
        vecs = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True)
        # normalize_embeddings=True already L2-normalizes for cosine/IP; keep consistent
        return vecs

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text])[0]
import os
from typing import Tuple
import faiss
import numpy as np
from filelock import FileLock
from app.config import settings

class FaissStore:
    """
    append-only FAISS index (on disk)
    Uses IndexFlatIP with normalized vectors (cosine) L2??? 
    """
    def __init__(self, index_path: str | None = None, lock_path: str | None = None):
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.lock_path = lock_path or settings.INDEX_LOCK_PATH
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        self._index = None  # loaded lazily

    def _read_index(self):
        if os.path.exists(self.index_path):
            self._index = faiss.read_index(self.index_path)
        else:
            self._index = None

    def _write_index(self):
        faiss.write_index(self._index, self.index_path)

    def _ensure_index(self, dim: int):
        if self._index is None:
            if os.path.exists(self.index_path):
                self._read_index()
            if self._index is None:
                self._index = faiss.IndexFlatIP(dim)

    def add(self, vectors: np.ndarray) -> Tuple[int, int]: #Returns (start_id, end_id_exclusive)

        if vectors.ndim != 2:
            raise ValueError("vectors must be 2D")
        dim = vectors.shape[1]
        with FileLock(self.lock_path):
            self._ensure_index(dim)
            if self._index.d != dim:
                raise ValueError(f"Vector dim mismatch: index={self._index.d}, given={dim}")
            start_id = self._index.ntotal
            self._index.add(vectors.astype(np.float32))
            self._write_index()
            end_id = self._index.ntotal
        return start_id, end_id

    def search(self, query: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, np.ndarray]: #Returns (scores, ids) as 1D arrays
        #Loads latest index and search.
        
        if query.ndim == 1:
            query = query.reshape(1, -1)
        with FileLock(self.lock_path, timeout=10):
            self._read_index()
            if self._index is None or self._index.ntotal == 0:
                return np.array([]), np.array([])
            if self._index.d != query.shape[1]:
                raise ValueError("Query dim mismatch")
            scores, ids = self._index.search(query.astype(np.float32), top_k)
        return scores[0], ids[0]

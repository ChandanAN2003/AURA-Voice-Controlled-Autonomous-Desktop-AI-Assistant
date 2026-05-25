import os
import json
import numpy as np
from typing import List
from backend.config import FAISS_INDEX_PATH
from utils.helpers import setup_logger

logger = setup_logger("VectorMemory")

# Path to store memory entries as plain text (alongside FAISS index)
MEMORY_STORE_PATH = FAISS_INDEX_PATH.replace(".bin", "_store.json")


class VectorMemory:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index_path = FAISS_INDEX_PATH
        self.memory_store: List[str] = []
        self._faiss_available = False
        self.index = None

        self._try_init_faiss()
        self._load_memory_store()

    def _try_init_faiss(self):
        """Attempt to initialize FAISS. If unavailable, fall back gracefully."""
        try:
            import faiss
            # Always create a fresh in-memory index (no binary file written —
            # FAISS C++ cannot handle non-ASCII chars like em-dash in Windows paths).
            self.index = faiss.IndexFlatL2(self.dimension)
            self._faiss_available = True
            logger.info("FAISS in-memory index created.")
        except ImportError:
            logger.warning("FAISS not installed. Vector memory will run in fallback (no similarity search) mode.")

    def _load_memory_store(self):
        """Load persisted text entries from disk."""
        if os.path.exists(MEMORY_STORE_PATH):
            try:
                with open(MEMORY_STORE_PATH, "r", encoding="utf-8") as f:
                    self.memory_store = json.load(f)
                logger.info(f"Loaded {len(self.memory_store)} memory entries from disk.")
            except Exception as e:
                logger.warning(f"Could not load memory store: {e}")
                self.memory_store = []

    def _save_memory_store(self):
        """Persist text entries to disk."""
        try:
            with open(MEMORY_STORE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.memory_store, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Could not save memory store: {e}")

    def _dummy_embed(self, text: str) -> np.ndarray:
        """Generate a deterministic pseudo-embedding from text hash."""
        np.random.seed(abs(hash(text)) % (2 ** 32))
        return np.random.rand(1, self.dimension).astype('float32')

    def add_memory(self, text: str):
        """Add a text entry to memory."""
        self.memory_store.append(text)
        self._save_memory_store()

        if self._faiss_available and self.index is not None:
            try:
                vector = self._dummy_embed(text)
                self.index.add(vector)
                logger.info(f"Added entry to FAISS index. Total entries: {self.index.ntotal}")
            except Exception as e:
                logger.error(f"Could not add to FAISS index: {e}")

    def search_memory(self, query: str, top_k: int = 3) -> List[str]:
        """Search memory for related entries."""
        if not self.memory_store:
            return []

        if self._faiss_available and self.index is not None and self.index.ntotal > 0:
            try:
                vector = self._dummy_embed(query)
                k = min(top_k, self.index.ntotal)
                distances, indices = self.index.search(vector, k)
                results = []
                for idx in indices[0]:
                    if idx != -1 and idx < len(self.memory_store):
                        results.append(self.memory_store[idx])
                return results
            except Exception as e:
                logger.error(f"FAISS search error: {e}")

        # Fallback: return the last top_k items
        return self.memory_store[-top_k:]

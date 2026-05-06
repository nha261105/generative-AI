"""
src/data_layer/embeddings.py
─────────────────────────────
Batch embedding wrapper cho sentence-transformers.

Kế thừa langchain_core.embeddings.Embeddings để tương thích hoàn toàn
với FAISS.from_documents(), FAISS constructor (embedding_function),
và mọi LangChain retriever.
"""

from __future__ import annotations

import os
from typing import List

import numpy as np
from langchain_core.embeddings import Embeddings

# Tắt tokenizer parallelism warning khi dùng multi-thread
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


class BatchEmbedder(Embeddings):
    """
    Drop-in replacement cho HuggingFaceEmbeddings với batch encoding tối ưu.

    Kế thừa langchain_core.embeddings.Embeddings — tương thích với:
      - FAISS.from_documents(chunks, embedder)
      - FAISS(embedding_function=embedder, ...)
      - vector_store.as_retriever()
      - EnsembleRetriever, BM25Retriever

    Args:
        model_name:  Tên model sentence-transformers
        batch_size:  Số texts encode mỗi lần forward pass (tune theo RAM)
        device:      "cpu" hoặc "cuda"
        normalize:   L2-normalize embeddings (khuyến nghị cho cosine similarity)
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        batch_size: int = 64,
        device: str = "cpu",
        normalize: bool = True,
    ):
        from sentence_transformers import SentenceTransformer

        self.batch_size = batch_size
        self.normalize = normalize
        self._model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Encode toàn bộ list texts trong một lần gọi encode()."""
        if not texts:
            return []
        
        import time
        t0 = time.perf_counter()
        
        embeddings: np.ndarray = self._model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        
        elapsed = time.perf_counter() - t0
        if elapsed > 0.5:  # Only log if significant
            print(f"  ⏱️  Embedded {len(texts)} documents: {elapsed:.3f}s")
        
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Encode single query — dùng khi retrieval."""
        import time
        t0 = time.perf_counter()
        
        embedding: np.ndarray = self._model.encode(
            [text],
            batch_size=1,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        
        elapsed = time.perf_counter() - t0
        if elapsed > 0.1:  # Only log if significant
            print(f"  ⏱️  Query embedding: {elapsed:.3f}s")
        
        return embedding[0].tolist()

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """
        FAISS constructor gọi embedding_function(texts) trực tiếp.
        Delegate về embed_documents để đảm bảo tương thích.
        """
        return self.embed_documents(texts)


def get_embedder(
    model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    device: str = "cpu",
    batch_size: int = 64,
) -> BatchEmbedder:
    return BatchEmbedder(model_name=model_name, device=device, batch_size=batch_size)

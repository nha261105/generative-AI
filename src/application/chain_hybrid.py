from langchain.retrievers import EnsembleRetriever

from src.data_layer.vector_store import (
    get_vector_retriever,
    get_bm25_retriever
)

from langchain_community.vectorstores import FAISS
from langchain.schema import Document

from typing import List


def create_hybrid_retriever(

        vector_store: FAISS,
        chunks: List[Document],
        k: int = 3

):

    # Vector retriever
    vector_retriever = get_vector_retriever(
        vector_store,
        k
    )

    # BM25 retriever
    bm25_retriever = get_bm25_retriever(
        chunks,
        k
    )   

    # Hybrid (Ensemble)
    hybrid_retriever = EnsembleRetriever(

        retrievers=[
            vector_retriever,
            bm25_retriever
        ],

        weights=[0.7,0.3]

    )

    return hybrid_retriever
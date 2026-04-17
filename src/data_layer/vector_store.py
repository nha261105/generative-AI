from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from typing import List
from langchain_core.documents import Document


def create_vector_store(
        chunks: List[Document],
        embedder: HuggingFaceEmbeddings
) -> FAISS:
    return FAISS.from_documents(chunks, embedder)


def _get_documents_from_vector_store(vector_store: FAISS) -> List[Document]:
    docstore = getattr(vector_store, "docstore", None)
    if docstore is None:
        return []

    raw_dict = getattr(docstore, "_dict", {})
    return [doc for doc in raw_dict.values() if isinstance(doc, Document)]


def get_retriever(
        vector_store: FAISS,
        k: int = 3
):
    return get_vector_retriever(vector_store=vector_store, k=k)


def get_vector_retriever(
        vector_store: FAISS,
        k: int = 3,
        fetch_k: int = 10,
):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k, "fetch_k": fetch_k},
    )


def get_bm25_retriever(
        chunks: List[Document],
        k: int = 3,
):
    retriever = BM25Retriever.from_documents(chunks)
    retriever.k = k
    return retriever


def create_hybrid_retriever_from_vector_store(
        vector_store: FAISS,
        k: int = 3,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
):
    chunks = _get_documents_from_vector_store(vector_store)
    if not chunks:
        return get_vector_retriever(vector_store=vector_store, k=k)

    vector_retriever = get_vector_retriever(vector_store=vector_store, k=k)
    bm25_retriever = get_bm25_retriever(chunks=chunks, k=k)

    return EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[vector_weight, bm25_weight],
    )



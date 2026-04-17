from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import List
from langchain.schema import Document


def create_vector_store(
        chunks: List[Document],
        embedder: HuggingFaceEmbeddings
) -> FAISS:

    return FAISS.from_documents(chunks,embedder)


def get_vector_retriever(
        vector_store: FAISS,
        k: int = 3
):

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )


def get_bm25_retriever(
        chunks: List[Document],
        k: int = 3
):
    # Build keyword index từ chunks
    bm25 = BM25Retriever.from_documents(chunks) 

    #Top k keyword matches
    bm25.k = k

    return bm25
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings;
from typing import List
from langchain.schema import Document

def create_vector_store(
        chunks: List[Document],
        embedder: HuggingFaceEmbeddings
) -> FAISS:
    return FAISS.aadd_documents(chunks,embedder)

def get_retriever(
        vector_store: FAISS,
        k: int = 3
):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )



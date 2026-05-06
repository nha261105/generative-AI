import os
import pickle
import faiss as faiss_lib

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_community.docstore.in_memory import InMemoryDocstore
from typing import List
from langchain_core.documents import Document


def create_vector_store(
        chunks: List[Document],
        embedder: HuggingFaceEmbeddings
) -> FAISS:
    return FAISS.from_documents(chunks, embedder)


def save_index(vector_store: FAISS, path: str) -> None:
    """
    Lưu FAISS index và docstore metadata ra disk.

    - index.faiss : raw FAISS index (dùng faiss.write_index)
    - index.pkl   : docstore._dict + index_to_docstore_id (pickle)

    Tách riêng thay vì dùng vector_store.save_local() để kiểm soát
    rõ ràng từng thành phần khi load lại.
    """
    os.makedirs(path, exist_ok=True)

    # Lưu FAISS binary index
    faiss_lib.write_index(vector_store.index, os.path.join(path, "index.faiss"))

    # Lưu metadata: docstore dict + mapping id → docstore key
    metadata = {
        "docstore_dict": vector_store.docstore._dict,
        "index_to_docstore_id": vector_store.index_to_docstore_id,
    }
    with open(os.path.join(path, "index.pkl"), "wb") as f:
        pickle.dump(metadata, f)


def load_if_exists(path: str, embedder: HuggingFaceEmbeddings) -> FAISS | None:
    """
    Load FAISS index từ disk nếu tồn tại.

    Trả về FAISS instance nếu thành công, None nếu chưa có hoặc lỗi.
    Nhận embedder để reconstruct đúng embedding function cho vector store.
    """
    faiss_path = os.path.join(path, "index.faiss")
    pkl_path = os.path.join(path, "index.pkl")

    if not (os.path.exists(faiss_path) and os.path.exists(pkl_path)):
        return None

    try:
        index = faiss_lib.read_index(faiss_path)

        with open(pkl_path, "rb") as f:
            metadata = pickle.load(f)

        docstore = InMemoryDocstore(metadata["docstore_dict"])
        vector_store = FAISS(
            embedding_function=embedder,
            index=index,
            docstore=docstore,
            index_to_docstore_id=metadata["index_to_docstore_id"],
        )
        return vector_store
    except Exception:
        return None


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

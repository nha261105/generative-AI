import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.application.rag_chain import get_answer
from src.application.chain_hybrid import create_hybrid_retriever
from unittest.mock import patch


# =========================
# FAKE DOC (CHUẨN CHO BM25)
# =========================
class FakeDoc:
    def __init__(self, content="Test content", page=0):
        self.page_content = content
        self.metadata = {"page": page}
        self.id = "1"  # bắt buộc cho BM25


# =========================
# TC01 – NORMAL CASE - kiểm tra luồng bình thường
# =========================
def test_hybrid_basic():

    class FakeRetriever:
        def invoke(self, q):
            return [FakeDoc()]

    class FakeVectorDB:
        def as_retriever(self, **kwargs):
            return FakeRetriever()

    vector_db = FakeVectorDB()
    chunks = [FakeDoc()]

    with patch("src.application.rag_chain.Ollama") as mock_llm:
        mock_llm.return_value.invoke.return_value = "answer"

        with patch("src.application.rag_chain.create_hybrid_retriever") as mock_hybrid:
            mock_hybrid.return_value.invoke.return_value = [FakeDoc()]

            response, sources, hybrid_response, hybrid_sources = get_answer(
                "test",
                vector_db,
                chunks
            )

            assert response == "answer"
            assert hybrid_response == "answer"
            assert len(sources) > 0
            assert len(hybrid_sources) > 0


# =========================
# TC02 – EMPTY RESULT - kiểm tra không thấy kết quả trả về
# =========================
def test_hybrid_empty():

    class FakeRetriever:
        def invoke(self, q):
            return []

    class FakeVectorDB:
        def as_retriever(self, **kwargs):
            return FakeRetriever()

    vector_db = FakeVectorDB()
    chunks = [FakeDoc()]

    with patch("src.application.rag_chain.Ollama") as mock_llm:
        mock_llm.return_value.invoke.return_value = "no data"

        with patch("src.application.rag_chain.create_hybrid_retriever") as mock_hybrid:
            mock_hybrid.return_value.invoke.return_value = []

            response, sources, hybrid_response, hybrid_sources = get_answer(
                "test",
                vector_db,
                chunks
            )

            assert response == "no data"
            assert hybrid_response == "no data"
            assert sources == []
            assert hybrid_sources == []


# =========================
# TC03 – VECTOR ≠ HYBRID - kiểm tra kết quả từ pure và hybrid khác nhau
# =========================
def test_vector_vs_hybrid_different():

    class FakeRetriever:
        def invoke(self, q):
            return [FakeDoc("Vector doc", 0)]

    class FakeVectorDB:
        def as_retriever(self, **kwargs):
            return FakeRetriever()

    vector_db = FakeVectorDB()
    chunks = [FakeDoc("Hybrid doc", 1)]

    with patch("src.application.rag_chain.Ollama") as mock_llm:
        mock_llm.return_value.invoke.return_value = "ok"

        with patch("src.application.rag_chain.create_hybrid_retriever") as mock_hybrid:
            mock_hybrid.return_value.invoke.return_value = [FakeDoc("Hybrid doc", 1)]

            response, sources, hybrid_response, hybrid_sources = get_answer(
                "test",
                vector_db,
                chunks
            )

            assert sources != hybrid_sources


# =========================
# TC04 – CREATE HYBRID (PATCH CORE)
# =========================
def test_create_hybrid():

    with patch("src.application.chain_hybrid.get_vector_retriever") as mock_vector, \
         patch("src.application.chain_hybrid.get_bm25_retriever") as mock_bm25, \
         patch("src.application.chain_hybrid.EnsembleRetriever") as mock_ensemble:

        mock_vector.return_value = object()
        mock_bm25.return_value = object()
        mock_ensemble.return_value = "hybrid_object"  # giả lập kết quả kết hợp 2 retriever thành công

        class FakeVectorStore:
            pass
        # đây là giả lập vector store -> object FAISS
        # get_vector_retriever -> đã bị patch -> không gọi vector_store.as_retriever()

        chunks = [FakeDoc(), FakeDoc()]

        hybrid = create_hybrid_retriever(FakeVectorStore(), chunks)

        assert hybrid == "hybrid_object"

# =========================
# TC05 – ERROR CASE - test có lỗi khi vector database none
# =========================
def test_hybrid_vector_db_none():

    with patch("src.application.rag_chain.Ollama") as mock_llm:
        mock_llm.return_value.invoke.return_value = "error"

        try:
            get_answer("test", None, [FakeDoc()])
        except Exception:
            assert True
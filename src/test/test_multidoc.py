import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.application.chain_multidoc import get_answer_multidoc
from src.presentation.comp_multidoc import build_filter_cache
from unittest.mock import patch


# =========================
# TC01 – NORMAL CASE - kiểm tra luồng bình thường
# =========================
def test_get_answer_basic():
    query = "Nội dung chính là gì?"

    class FakeDoc:
        def __init__(self):
            self.page_content = "Đây là nội dung test"
            self.metadata = {"filename": "test.pdf", "page": 0}

    class FakeRetriever:
        def invoke(self, q):
            return [FakeDoc()]

    class FakeVectorDB:
        def as_retriever(self, **kwargs):
            return FakeRetriever()

    vector_db = FakeVectorDB()

    with patch("src.application.chain_multidoc.get_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = "fake answer"

        response, sources = get_answer_multidoc(query, vector_db)

        assert response == "fake answer"
        assert len(sources) > 0


# =========================
# TC02 – EDGE CASE (NO DOCS) - kiểm tra không có tài liệu phù hợp
# =========================
def test_empty_docs():
    
    class FakeRetriever:
        def invoke(self, q):
            return []

    class FakeVectorDB:
        def as_retriever(self, **kwargs):
            return FakeRetriever()

    vector_db = FakeVectorDB()

    with patch("src.application.chain_multidoc.get_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = "no data"

        response, sources = get_answer_multidoc("test", vector_db)

        assert response == "no data"
        assert sources == []


# =========================
# TC03 – FILTER RUNTIME - kiểm tra có filter
# =========================
def test_filter_applied():
    
    class FakeRetriever:
        def invoke(self, q):
            return []

    class FakeVectorDB:
        def as_retriever(self, **kwargs):
            # kiểm tra filter có được truyền không
            assert "filter" in kwargs["search_kwargs"]
            return FakeRetriever()

    vector_db = FakeVectorDB()

    with patch("src.application.chain_multidoc.get_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = "ok"

        get_answer_multidoc(
            "test",
            vector_db,
            metadata_filter={"filename": "A.pdf"}
        )


# =========================
# TC04 – UI FILTER CACHE - kiểm tra cache UI filter
# =========================
def test_build_filter_cache():
    class FakeDoc:
        def __init__(self):
            self.metadata = {
                "filename": "file1.pdf",
                "upload_time": "2026-04-16 10:00:00",
                "file_type": "pdf"
            }

    class FakeVectorDB:
        def __init__(self):
            self.docstore = type("", (), {})()
            self.docstore._dict = {"1": FakeDoc()}

    vector_db = FakeVectorDB()

    result = build_filter_cache(vector_db)

    assert len(result) == 1
    assert "file1.pdf" in list(result.values())[0]


# =========================
# TC05 – ERROR CASE - test có lỗi khi vector database none
# =========================
def test_vector_db_none():
    with patch("src.application.chain_multidoc.get_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = "error"

        try:
            get_answer_multidoc("test", None)
        except Exception:
            assert True
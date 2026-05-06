from typing import Dict, List, Tuple
from langchain_core.documents import Document

from src.application.chain_base import BaseRAGChain


class MultiDocRAGChain(BaseRAGChain):
    """RAG chain với metadata filtering cho multi-document."""
    
    @staticmethod
    def _filter_docs_manually(docs: List[Document], filenames: List[str]) -> List[Document]:
        """Filter documents by a list of filenames (for multi-select filter)."""
        return [
            doc for doc in docs
            if (doc.metadata.get("filename") or doc.metadata.get("source", "").split("/")[-1])
            in filenames
        ]
    
    def get_answer(
        self,
        query: str,
        vector_db,
        chat_history: List[Dict] | None = None,
        metadata_filter: Dict | None = None,
    ) -> Tuple[str, List[Dict]]:
        search_kwargs = {"k": 4, "fetch_k": 12}
        
        # Determine filter approach
        multi_filenames = None
        if metadata_filter:
            filenames_value = metadata_filter.get("filename")
            if isinstance(filenames_value, list):
                # Multi-file filter — FAISS doesn't support OR filter natively
                multi_filenames = filenames_value
                search_kwargs["k"] = 8
            elif filenames_value:
                # Single file → FAISS exact match filter
                search_kwargs["filter"] = {"filename": filenames_value}
        
        retriever = vector_db.as_retriever(
            search_type="mmr",
            search_kwargs=search_kwargs,
        )
        docs = retriever.invoke(query)
        
        # Manual multi-file filter
        if multi_filenames:
            docs = self._filter_docs_manually(docs, multi_filenames)
        
        if not docs:
            return (
                "Mình chưa tìm thấy ngữ cảnh phù hợp với bộ lọc tài liệu hiện tại. "
                "Bạn hãy thử chọn 'Tất cả' hoặc đặt lại câu hỏi cụ thể hơn.",
                [{
                    "id": 1,
                    "page": "?",
                    "content": "Không tìm thấy đoạn trích phù hợp cho bộ lọc hiện tại.",
                    "source_file": "Không xác định",
                }],
            )
        
        context_string, sources = self.build_context_and_sources(docs)
        response = self.generate_answer(query, context_string, chat_history)
        return response, sources


# Backward compatibility
def get_answer_multidoc(query: str, vector_db, metadata_filter=None):
    chain = MultiDocRAGChain()
    return chain.get_answer(query, vector_db, metadata_filter=metadata_filter)
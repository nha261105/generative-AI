"""
src/application/chain_base.py
──────────────────────────────
Base class chung cho tất cả RAG chains để giảm code trùng lặp.
"""

from typing import Dict, List, Tuple
from abc import ABC, abstractmethod

from src.application.prompts import get_rag_prompt, get_rag_prompt_with_history
from src.model_layer.cache import get_cached_llm


class BaseRAGChain(ABC):
    """
    Base class cho tất cả RAG chains.
    
    Cung cấp:
    - Format chat history
    - Build context và sources từ documents
    - Generate answer với LLM
    - Normalize sources schema
    """
    
    def __init__(self, temperature: float = 0.7):
        self.llm = get_cached_llm(temperature=temperature)
    
    @staticmethod
    def format_chat_history(chat_history: List[Dict] | None, max_turns: int = 2) -> str:
        """Format lịch sử hội thoại thành string. OPTIMIZED: 3→2 turns."""
        if not chat_history:
            return "(Chưa có lịch sử hội thoại)"
        
        recent_turns = chat_history[-max_turns:]
        lines: List[str] = []
        for turn in recent_turns:
            question = (turn.get("question") or "").strip()
            answer = (turn.get("answer") or "").strip()
            if question:
                lines.append(f"Người dùng: {question}")
            if answer:
                lines.append(f"Trợ lý: {answer}")
        return "\n".join(lines) if lines else "(Chưa có lịch sử hội thoại)"
    
    @staticmethod
    def build_context_and_sources(docs) -> Tuple[str, List[Dict]]:
        """
        Build context string và sources list từ retrieved documents.
        
        Returns:
            (context_string, sources_list)
        """
        context_list: List[str] = []
        sources: List[Dict] = []
        
        for i, doc in enumerate(docs, start=1):
            raw_page = doc.metadata.get("page", 0)
            page_num = raw_page + 1 if isinstance(raw_page, int) else (raw_page or "?")
            source_file = str(
                doc.metadata.get("filename")
                or doc.metadata.get("source")
                or "Tài liệu"
            ).split("/")[-1]
            
            context_list.append(f"[Nguồn {i} | Trang {page_num}]: {doc.page_content}")
            sources.append({
                "id": i,
                "page": page_num,
                "content": doc.page_content,
                "source_file": source_file,
            })
        
        return "\n\n".join(context_list), sources
    
    def generate_answer(
        self,
        query: str,
        context_string: str,
        chat_history: List[Dict] | None = None,
        use_cache: bool = True,  # NEW: Enable caching by default
    ) -> str:
        """Generate answer từ LLM với context và optional chat history."""
        import time
        from src.model_layer.cache import get_llm_response_with_cache
        
        t0 = time.perf_counter()
        
        if chat_history:
            prompt = get_rag_prompt_with_history().format(
                chat_history=self.format_chat_history(chat_history),
                context=context_string,
                question=query,
            )
        else:
            prompt = get_rag_prompt().format(
                context=context_string,
                question=query,
            )
        
        print(f"  ⏱️  Prompt formatting: {time.perf_counter() - t0:.3f}s")
        
        # Use cached response for repeated queries
        t_llm = time.perf_counter()
        response = get_llm_response_with_cache(prompt, temperature=self.llm.temperature, use_cache=use_cache)
        print(f"  ⏱️  LLM invoke: {time.perf_counter() - t_llm:.3f}s")
        
        return response
    
    @staticmethod
    def get_empty_response() -> Tuple[str, List[Dict]]:
        """Response mặc định khi không tìm thấy documents."""
        return (
            "Mình chưa tìm thấy ngữ cảnh phù hợp trong tài liệu đã index để trả lời an toàn. "
            "Bạn hãy thử diễn đạt lại câu hỏi hoặc upload thêm tài liệu liên quan.",
            [{
                "id": 1,
                "page": "?",
                "content": "Không tìm thấy đoạn trích phù hợp trong tài liệu hiện tại.",
                "source_file": "Không xác định"
            }],
        )
    
    @abstractmethod
    def get_answer(
        self,
        query: str,
        vector_db,
        chat_history: List[Dict] | None = None,
        **kwargs
    ) -> Tuple[str, List[Dict]]:
        """
        Abstract method - mỗi chain implement logic retrieval riêng.
        
        Returns:
            (answer_text, sources_list)
        """
        pass

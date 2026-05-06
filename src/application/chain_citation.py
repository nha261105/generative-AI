from typing import Tuple, List, Dict
import time
from src.application.chain_base import BaseRAGChain


class CitationRAGChain(BaseRAGChain):
    """RAG chain với citation tracking - semantic search cơ bản."""
    
    def get_answer(
        self,
        query: str,
        vector_db,
        chat_history: List[Dict] | None = None,
        k: int = 3,
        fetch_k: int = 10,
    ) -> Tuple[str, List[Dict]]:
        # Retriever creation
        t_retriever = time.perf_counter()
        retriever = vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k, "fetch_k": fetch_k},
        )
        print(f"  ⏱️  Retriever creation: {time.perf_counter() - t_retriever:.3f}s")
        
        # Retrieval (embedding + search)
        t_invoke = time.perf_counter()
        docs = retriever.invoke(query)
        print(f"  ⏱️  Retrieval invoke: {time.perf_counter() - t_invoke:.3f}s ({len(docs)} docs)")
        
        if not docs:
            return self.get_empty_response()
        
        # Context building
        t_context = time.perf_counter()
        context_string, sources = self.build_context_and_sources(docs)
        print(f"  ⏱️  Context building: {time.perf_counter() - t_context:.3f}s")
        
        # LLM generation
        t_llm = time.perf_counter()
        response = self.generate_answer(query, context_string, chat_history)
        print(f"  ⏱️  LLM generation: {time.perf_counter() - t_llm:.3f}s")
        
        return response, sources


# Backward compatibility - giữ function signature cũ
def get_answer_with_citation(
    query: str,
    vector_db,
    chat_history: List[Dict] | None = None,
) -> Tuple[str, List[Dict]]:
    chain = CitationRAGChain()
    return chain.get_answer(query, vector_db, chat_history)

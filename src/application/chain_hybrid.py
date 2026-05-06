from typing import List, Dict, Tuple
from src.application.chain_base import BaseRAGChain
from src.data_layer.vector_store import create_hybrid_retriever_from_vector_store


class HybridRAGChain(BaseRAGChain):
    """RAG chain với hybrid search (BM25 + Vector)."""
    
    def get_answer(
        self,
        query: str,
        vector_db,
        chat_history: List[Dict] | None = None,
        k: int = 3,
    ) -> Tuple[str, List[Dict]]:
        retriever = create_hybrid_retriever_from_vector_store(vector_store=vector_db, k=k)
        docs = retriever.invoke(query)
        
        if not docs:
            return self.get_empty_response()
        
        context_string, sources = self.build_context_and_sources(docs)
        response = self.generate_answer(query, context_string, chat_history)
        return response, sources


# Backward compatibility
def get_answer_with_hybrid_citation(
    query: str,
    vector_store,
    chat_history: List[Dict] | None = None,
    k: int = 3,
) -> Tuple[str, List[Dict]]:
    chain = HybridRAGChain()
    return chain.get_answer(query, vector_store, chat_history, k=k)
"""
src/application/rag_coordinator.py
───────────────────────────────────
Composable RAG pipeline coordinator.
Refactored to use strategy pattern for cleaner code.
"""

import time
from typing import Dict, List, Tuple, Optional

from src.utils.doc_helpers import doc_snippet
from src.application.rag_strategies import (
    maybe_rewrite_query,
    retrieve_docs,
    rerank_docs,
    generate_selfrag_answer,
    generate_standard_answer,
)


def execute(
    query: str,
    vdb,
    ctx: List[Dict],
    search_mode: str,
    use_rerank: bool,
    use_selfrag: bool,
    meta_filter: Optional[Dict] = None,
) -> Tuple[str, List, Dict]:
    """
    Composable pipeline: (conv-rewrite) → search → (rerank) → (self-rag) → LLM.
    
    Args:
        query: User query
        vdb: Vector database
        ctx: Chat history
        search_mode: "semantic" or "hybrid"
        use_rerank: Enable reranking
        use_selfrag: Enable Self-RAG
        meta_filter: Optional metadata filter
    
    Returns:
        Tuple of (response, sources, debug_info)
    """
    debug = {
        "pipeline": "",
        "timing": {},
        "pre_rerank_docs": [],
        "post_rerank_docs": []
    }
    pipe_parts = []
    t_total = time.perf_counter()
    
    # Step 1: Query rewrite (conditional)
    search_query = maybe_rewrite_query(query, ctx, use_selfrag, debug, pipe_parts)
    
    # Step 2: Retrieval
    response, docs, early_debug = retrieve_docs(
        search_query, vdb, search_mode, use_rerank, use_selfrag,
        meta_filter, ctx, debug, pipe_parts, t_total
    )
    
    # Early return if retrieval handled everything
    if early_debug is not None:
        return response, docs, early_debug
    
    # Pre-rerank debug
    for i, doc in enumerate(docs, 1):
        d = doc_snippet(doc)
        d["id"] = i
        d["score"] = None
        debug["pre_rerank_docs"].append(d)
    
    # Step 3: Reranking (optional)
    if use_rerank:
        docs = rerank_docs(search_query, docs, debug, pipe_parts)
    
    # Step 4: Answer generation
    if use_selfrag:
        return generate_selfrag_answer(query, docs, vdb, ctx, debug, pipe_parts, t_total)
    else:
        return generate_standard_answer(query, docs, ctx, debug, pipe_parts, t_total)

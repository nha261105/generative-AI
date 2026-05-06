"""
src/application/query_handler.py
─────────────────────────────────
Centralized query handling logic extracted from app.py.
Separates business logic from UI code.
"""

import importlib
import concurrent.futures
from typing import Dict, List, Tuple, Optional

from src.application.rag_coordinator import execute as run_pipeline
from src.utils.doc_helpers import normalize_sources, build_source_text
from src.utils.logger import log_query_start, log_query_end


def handle_standard_query(
    question: str,
    vector_db,
    chat_history: List[Dict],
    search_mode: str,
    use_rerank: bool,
    use_selfrag: bool,
    meta_filter: Optional[Dict] = None,
) -> Tuple[str, List[Dict], str, Dict]:
    """
    Handle standard RAG query.
    
    Args:
        question: User query
        vector_db: Vector store instance
        chat_history: Conversation history
        search_mode: "semantic" or "hybrid"
        use_rerank: Enable reranking
        use_selfrag: Enable Self-RAG
        meta_filter: Optional metadata filter for multi-doc
    
    Returns:
        Tuple of (response_text, sources_list, source_text, debug_info)
    """
    # Log query start
    log_query_start(question)
    
    response, raw_sources, debug = run_pipeline(
        question, vector_db, chat_history,
        search_mode, use_rerank, use_selfrag,
        meta_filter=meta_filter
    )
    
    sources = normalize_sources(raw_sources)
    source_text = build_source_text(sources)
    
    # Add original query to debug for logging
    debug["original_query"] = question
    
    # Log query end with summary
    log_query_end(debug)
    
    return response, sources, source_text, debug


def handle_comparison_query(
    question: str,
    vector_db,
    chat_history: List[Dict],
    search_mode: str,
    use_rerank: bool,
    use_selfrag: bool,
) -> Tuple[str, List[Dict], str, Dict, Dict]:
    """
    Handle RAG vs GraphRAG comparison query with parallel execution.
    
    Args:
        question: User query
        vector_db: Vector store instance
        chat_history: Conversation history
        search_mode: "semantic" or "hybrid"
        use_rerank: Enable reranking
        use_selfrag: Enable Self-RAG
    
    Returns:
        Tuple of (response_text, sources_list, source_text, debug_info, graph_comparison)
    """
    # Log query start
    log_query_start(f"{question} [COMPARISON MODE]")
    
    # Run RAG and GraphRAG in parallel
    def run_rag():
        return run_pipeline(
            question, vector_db, chat_history,
            search_mode, use_rerank, use_selfrag
        )
    
    def run_graphrag():
        gm = importlib.import_module("src.application.chain_graphrag")
        return gm.get_answer_with_graphrag_citation(
            question, vector_db, chat_history=chat_history
        )
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_rag = executor.submit(run_rag)
        future_graph = executor.submit(run_graphrag)
        
        vr, vs, vdbg = future_rag.result()
        gr, gs, gst = future_graph.result()
    
    # Calculate timing
    vt = vdbg.get("timing", {}).get("total", 0)
    gt = gst.get("total_time_sec", 0)
    total_parallel_time = max(vt, gt)
    
    # Normalize sources
    vsn = normalize_sources(vs)
    gsn = normalize_sources(gs)
    
    # Calculate overlap
    overlap = len(
        set((s["source_file"], s["page"]) for s in vsn) &
        set((s["source_file"], s["page"]) for s in gsn)
    )
    
    # Build comparison object
    graph_comparison = {
        "query": question,
        "vector": {
            "text": vr,
            "source": build_source_text(vsn),
            "sources": vsn,
            "query": question,
            "time": round(vt, 2)
        },
        "graphrag": {
            "text": gr,
            "source": build_source_text(gsn),
            "sources": gsn,
            "query": question,
            "time": round(gt, 2)
        },
        "overlap": overlap,
        "parallel_time": round(total_parallel_time, 2),
    }
    
    # Add original query to debug
    vdbg["original_query"] = question
    
    # Log comparison summary
    print(f"\n{'='*60}")
    print(f"📊 COMPARISON SUMMARY")
    print(f"{'='*60}")
    print(f"RAG Time: {vt:.3f}s")
    print(f"GraphRAG Time: {gt:.3f}s")
    print(f"Parallel Time: {total_parallel_time:.3f}s (saved {vt + gt - total_parallel_time:.3f}s)")
    print(f"Source Overlap: {overlap} documents")
    print(f"{'='*60}\n")
    
    # Log query end
    log_query_end(vdbg)
    
    return vr, vsn, build_source_text(vsn), vdbg, graph_comparison


def create_benchmark_log_entry(
    benchmark_type: str,
    query: str,
    **kwargs
) -> Dict:
    """
    Create standardized benchmark log entry.
    
    Args:
        benchmark_type: "compare", "chunk", or "query"
        query: User query (truncated to 30 chars)
        **kwargs: Additional benchmark data
    
    Returns:
        Dict with benchmark data
    """
    entry = {
        "benchmark_type": benchmark_type,
        "query": query[:30] + "..." if len(query) > 30 else query,
    }
    entry.update(kwargs)
    return entry

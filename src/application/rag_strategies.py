"""
src/application/rag_strategies.py
──────────────────────────────────
Strategy pattern for different RAG retrieval methods.
Simplifies rag_coordinator.py by extracting retrieval logic.
"""

import time
from typing import List, Tuple, Dict, Optional

from src.model_layer.cache import get_cached_llm
from src.utils.doc_helpers import doc_snippet


def maybe_rewrite_query(
    query: str,
    chat_history: List[Dict],
    use_selfrag: bool,
    debug: Dict,
    pipe_parts: List[str],
) -> str:
    """
    Conditionally rewrite query if it contains pronouns and has chat history.
    
    Args:
        query: Original query
        chat_history: Conversation history
        use_selfrag: If True, skip rewrite (Self-RAG handles it)
        debug: Debug dict to update
        pipe_parts: Pipeline parts list to update
    
    Returns:
        Rewritten query or original query
    """
    PRONOUNS = [
        "nó", "anh ấy", "cô ấy", "họ", "đó", "này", "cái đó",
        "it", "he", "she", "they", "this", "that", "those"
    ]
    
    def needs_rewrite(q: str) -> bool:
        q_lower = q.lower()
        return any(pronoun in q_lower for pronoun in PRONOUNS)
    
    if not chat_history or use_selfrag or not needs_rewrite(query):
        debug["rewrite_triggered"] = False
        return query
    
    t0 = time.perf_counter()
    from src.application.chain_selfrag import _format_chat_history
    from src.application.prompts import get_self_rag_rewrite_prompt
    
    llm_rewrite = get_cached_llm(temperature=0.1)
    rewritten = str(llm_rewrite.invoke(get_self_rag_rewrite_prompt().format(
        question=query,
        chat_history=_format_chat_history(chat_history, max_turns=2)
    ))).strip()
    
    debug["timing"]["conv_rewrite"] = round(time.perf_counter() - t0, 3)
    debug["rewritten_query"] = rewritten
    debug["rewrite_triggered"] = True
    pipe_parts.append("conv-rewrite")
    
    return rewritten


def retrieve_docs(
    query: str,
    vector_db,
    search_mode: str,
    use_rerank: bool,
    use_selfrag: bool,
    meta_filter: Optional[Dict],
    chat_history: List[Dict],
    debug: Dict,
    pipe_parts: List[str],
    t_total: float,
) -> Tuple[Optional[str], Optional[List], Optional[Dict]]:
    """
    Retrieve documents using specified search mode.
    
    Returns:
        Tuple of (response, sources, debug) if early return, else (None, docs, None)
    """
    # Multi-doc filter (early return)
    if meta_filter:
        t0 = time.perf_counter()
        print(f"  🔍 Starting multi-doc retrieval...")
        from src.application.chain_multidoc import get_answer_multidoc
        response, raw_sources = get_answer_multidoc(query, vector_db, metadata_filter=meta_filter)
        elapsed = round(time.perf_counter() - t0, 3)
        debug["timing"]["multidoc"] = elapsed
        print(f"  ⏱️  Multi-doc retrieval: {elapsed:.3f}s")
        pipe_parts.append("multidoc")
        debug["pipeline"] = " → ".join(pipe_parts)
        debug["timing"]["total"] = round(time.perf_counter() - t_total, 3)
        return response, raw_sources, debug
    
    # Hybrid search
    if search_mode == "hybrid":
        t0 = time.perf_counter()
        if not use_rerank and not use_selfrag:
            print(f"  🔍 Starting hybrid search + LLM...")
            from src.application.chain_hybrid import get_answer_with_hybrid_citation
            response, raw_sources = get_answer_with_hybrid_citation(query, vector_db, chat_history=chat_history)
            elapsed = round(time.perf_counter() - t0, 3)
            debug["timing"]["hybrid_search+llm"] = elapsed
            print(f"  ⏱️  Hybrid search + LLM: {elapsed:.3f}s")
            pipe_parts.append("hybrid")
            debug["pipeline"] = " → ".join(pipe_parts)
            debug["timing"]["total"] = round(time.perf_counter() - t_total, 3)
            return response, raw_sources, debug
        else:
            print(f"  🔍 Starting hybrid retrieval...")
            from src.data_layer.vector_store import create_hybrid_retriever_from_vector_store
            retriever = create_hybrid_retriever_from_vector_store(vector_db, k=8 if use_rerank else 5)
            docs = retriever.invoke(query)
            elapsed = round(time.perf_counter() - t0, 3)
            debug["timing"]["hybrid_retrieve"] = elapsed
            print(f"  ⏱️  Hybrid retrieval: {elapsed:.3f}s ({len(docs)} docs)")
            pipe_parts.append("hybrid")
            return None, docs, None
    
    # Semantic search
    t0 = time.perf_counter()
    if not use_rerank and not use_selfrag:
        print(f"  🔍 Starting semantic search + LLM...")
        from src.application.chain_citation import get_answer_with_citation
        
        # Track embedding time separately
        t_embed = time.perf_counter()
        response, raw_sources = get_answer_with_citation(query, vector_db, chat_history=chat_history)
        elapsed = round(time.perf_counter() - t0, 3)
        
        debug["timing"]["semantic_search+llm"] = elapsed
        print(f"  ⏱️  Semantic search + LLM: {elapsed:.3f}s")
        pipe_parts.append("semantic")
        debug["pipeline"] = " → ".join(pipe_parts)
        debug["timing"]["total"] = round(time.perf_counter() - t_total, 3)
        return response, raw_sources, debug
    else:
        print(f"  🔍 Starting semantic retrieval...")
        t_retriever_create = time.perf_counter()
        retriever = vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 8 if use_rerank else 5, "fetch_k": 20}
        )
        print(f"  ⏱️  Retriever creation: {time.perf_counter() - t_retriever_create:.3f}s")
        
        t_invoke = time.perf_counter()
        docs = retriever.invoke(query)
        invoke_time = time.perf_counter() - t_invoke
        print(f"  ⏱️  Retriever invoke (embedding + search): {invoke_time:.3f}s ({len(docs)} docs)")
        
        elapsed = round(time.perf_counter() - t0, 3)
        debug["timing"]["semantic_retrieve"] = elapsed
        debug["timing"]["retriever_invoke"] = round(invoke_time, 3)
        pipe_parts.append("semantic")
        return None, docs, None


def rerank_docs(
    query: str,
    docs: List,
    debug: Dict,
    pipe_parts: List[str],
) -> List:
    """
    Rerank documents using CrossEncoder.
    
    Args:
        query: Search query
        docs: Retrieved documents
        debug: Debug dict to update
        pipe_parts: Pipeline parts list to update
    
    Returns:
        Reranked documents (top 5)
    """
    from src.model_layer.cache import get_cached_reranker
    
    t0 = time.perf_counter()
    reranker = get_cached_reranker()
    pairs = [(query, doc.page_content) for doc in docs]
    scores = reranker.predict(pairs)
    
    # Update debug with scores
    for i, score in enumerate(scores):
        if i < len(debug["pre_rerank_docs"]):
            debug["pre_rerank_docs"][i]["score"] = float(score)
    
    # Sort and take top 5
    ranked = sorted(zip(docs, scores), key=lambda x: float(x[1]), reverse=True)
    top_docs = [doc for doc, _ in ranked[:5]]
    
    # Post-rerank debug
    for i, (doc, score) in enumerate(ranked[:5], 1):
        d = doc_snippet(doc)
        d["id"] = i
        d["score"] = float(score)
        debug["post_rerank_docs"].append(d)
    
    debug["timing"]["rerank"] = round(time.perf_counter() - t0, 3)
    pipe_parts.append("rerank")
    
    return top_docs


def generate_selfrag_answer(
    query: str,
    docs: List,
    vector_db,
    chat_history: List[Dict],
    debug: Dict,
    pipe_parts: List[str],
    t_total: float,
) -> Tuple[str, List, Dict]:
    """
    Generate answer using Self-RAG.
    
    Returns:
        Tuple of (answer_text, sources, debug)
    """
    t0 = time.perf_counter()
    from src.application.chain_selfrag import (
        _build_context_and_sources, _answer_with_context,
        _extract_json_payload,
    )
    from src.application.prompts import get_self_rag_eval_and_rewrite_prompt
    from src.model_layer.cache import get_cached_llm
    
    llm = get_cached_llm(temperature=0.3)
    context_str, sources = _build_context_and_sources(docs)
    answer = _answer_with_context(llm, query, context_str, chat_history)
    
    # Combined eval + rewrite
    from src.application.chain_selfrag import _format_chat_history
    
    eval_raw = llm.invoke(get_self_rag_eval_and_rewrite_prompt().format(
        question=query,
        chat_history=_format_chat_history(chat_history) if chat_history else "",
        context=context_str,
        answer=answer
    ))
    payload = _extract_json_payload(eval_raw)
    confidence = max(0.0, min(1.0, float(payload.get("confidence", 0.5))))
    needs_rewrite = bool(payload.get("needs_rewrite", False))
    rewritten = str(payload.get("rewritten_query", "")).strip()
    
    debug["confidence"] = confidence
    debug["hops_used"] = 1
    
    # Hop 2 if needed
    if needs_rewrite or confidence < 0.62:
        debug["hops_used"] = 2
        if rewritten:
            docs2 = vector_db.as_retriever(search_kwargs={"k": 5}).invoke(rewritten)
            if docs2:
                ctx2, src2 = _build_context_and_sources(docs2)
                ans2 = _answer_with_context(llm, rewritten, ctx2, chat_history)
                answer = llm.invoke(
                    f"Tổng hợp:\nCÂU HỎI: {query}\n"
                    f"HOP 1: {answer}\nHOP 2 (rewrite: {rewritten}): {ans2}\n"
                    f"Trả lời dựa trên cả 2 hop, trích dẫn [Nguồn X]."
                )
                sources = sources + src2
                for i, s in enumerate(sources, 1):
                    s["id"] = i
                confidence = 0.7
    
    answer_text = (f"{answer}\n\n(Self-RAG: {debug['hops_used']} hop · "
                   f"confidence: {confidence:.0%})")
    
    debug["timing"]["selfrag"] = round(time.perf_counter() - t0, 3)
    pipe_parts.append("self-rag")
    debug["pipeline"] = " → ".join(pipe_parts)
    debug["timing"]["total"] = round(time.perf_counter() - t_total, 3)
    
    return answer_text, sources, debug


def generate_standard_answer(
    query: str,
    docs: List,
    chat_history: List[Dict],
    debug: Dict,
    pipe_parts: List[str],
    t_total: float,
) -> Tuple[str, List, Dict]:
    """
    Generate standard answer without Self-RAG.
    
    Returns:
        Tuple of (answer_text, sources, debug)
    """
    t0 = time.perf_counter()
    print(f"  🤖 Starting LLM generation...")
    from src.application.chain_selfrag import _build_context_and_sources, _answer_with_context
    from src.model_layer.cache import get_cached_llm
    
    t_llm_load = time.perf_counter()
    llm = get_cached_llm(temperature=0.7)
    llm_load_time = time.perf_counter() - t_llm_load
    if llm_load_time > 0.1:
        print(f"  ⏱️  LLM load: {llm_load_time:.3f}s")
        debug["timing"]["llm_load"] = round(llm_load_time, 3)
    
    t_context = time.perf_counter()
    context_str, sources = _build_context_and_sources(docs)
    context_time = time.perf_counter() - t_context
    print(f"  ⏱️  Context building: {context_time:.3f}s")
    debug["timing"]["context_build"] = round(context_time, 3)
    
    t_invoke = time.perf_counter()
    response = _answer_with_context(llm, query, context_str, chat_history)
    invoke_time = time.perf_counter() - t_invoke
    print(f"  ⏱️  LLM invoke: {invoke_time:.3f}s")
    debug["timing"]["llm_invoke"] = round(invoke_time, 3)
    
    elapsed = round(time.perf_counter() - t0, 3)
    debug["timing"]["llm"] = elapsed
    print(f"  ⏱️  Total generation: {elapsed:.3f}s")
    pipe_parts.append("llm")
    debug["pipeline"] = " → ".join(pipe_parts)
    debug["timing"]["total"] = round(time.perf_counter() - t_total, 3)
    
    return response, sources, debug

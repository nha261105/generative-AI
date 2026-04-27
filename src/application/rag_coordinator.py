import time
import importlib
from functools import lru_cache

def _doc_snippet(doc, max_len=120) -> dict:
    """Build a debug-friendly doc dict."""
    meta = doc.metadata or {}
    raw_page = meta.get("page", 0)
    page = raw_page + 1 if isinstance(raw_page, int) else (raw_page or "?")
    fname = str(meta.get("filename") or meta.get("source") or "?").split("/")[-1]
    text = (doc.page_content or "")[:max_len].replace("\n", " ")
    return {"file": fname, "page": page, "snippet": text}

def execute(query, vdb, ctx, search_mode, use_rerank, use_selfrag, meta_filter=None):
    """Composable pipeline: (conv-rewrite) → search → (rerank) → (self-rag) → LLM."""
    debug = {"pipeline": "", "timing": {}, "pre_rerank_docs": [], "post_rerank_docs": []}
    pipe_parts = []
    t_total = time.perf_counter()

    # Step 0: Conversational Query Rewrite (Memory Buffer)
    search_query = query
    if ctx and not use_selfrag:
        t0 = time.perf_counter()
        from src.application.chain_selfrag import _format_chat_history
        from src.application.prompts import get_self_rag_rewrite_prompt
        from langchain_community.llms import Ollama
        
        llm_rewrite = Ollama(model="qwen2.5:7b", temperature=0.1)
        search_query = str(llm_rewrite.invoke(get_self_rag_rewrite_prompt().format(
            question=query, chat_history=_format_chat_history(ctx)))).strip()
        debug["timing"]["conv_rewrite"] = time.perf_counter() - t0
        pipe_parts.append("conv-rewrite")
        debug["rewritten_query"] = search_query

    # Step 1: Retrieval
    if meta_filter:
        t0 = time.perf_counter()
        from src.application.chain_multidoc import get_answer_multidoc
        response, raw_sources = get_answer_multidoc(search_query, vdb, metadata_filter=meta_filter)
        debug["timing"]["multidoc"] = time.perf_counter() - t0
        pipe_parts.append("multidoc")
        debug["pipeline"] = " → ".join(pipe_parts)
        debug["timing"]["total"] = time.perf_counter() - t_total
        return response, raw_sources, debug

    if search_mode == "hybrid":
        t0 = time.perf_counter()
        if not use_rerank and not use_selfrag:
            from src.application.chain_hybrid import get_answer_with_hybrid_citation
            response, raw_sources = get_answer_with_hybrid_citation(search_query, vdb, chat_history=ctx)
            debug["timing"]["hybrid_search+llm"] = time.perf_counter() - t0
            pipe_parts.append("hybrid")
            debug["pipeline"] = " → ".join(pipe_parts)
            debug["timing"]["total"] = time.perf_counter() - t_total
            return response, raw_sources, debug
        else:
            # Need raw docs for rerank/selfrag — use hybrid retriever only
            from src.data_layer.vector_store import create_hybrid_retriever_from_vector_store
            retriever = create_hybrid_retriever_from_vector_store(vdb, k=12 if use_rerank else 5)
            docs = retriever.invoke(search_query)
            debug["timing"]["hybrid_retrieve"] = time.perf_counter() - t0
            pipe_parts.append("hybrid")
    else:
        t0 = time.perf_counter()
        if not use_rerank and not use_selfrag:
            from src.application.chain_citation import get_answer_with_citation
            response, raw_sources = get_answer_with_citation(search_query, vdb, chat_history=ctx)
            debug["timing"]["semantic_search+llm"] = time.perf_counter() - t0
            pipe_parts.append("semantic")
            debug["pipeline"] = " → ".join(pipe_parts)
            debug["timing"]["total"] = time.perf_counter() - t_total
            return response, raw_sources, debug
        else:
            retriever = vdb.as_retriever(search_type="similarity",
                                          search_kwargs={"k": 12 if use_rerank else 5, "fetch_k": 20})
            docs = retriever.invoke(search_query)
            debug["timing"]["semantic_retrieve"] = time.perf_counter() - t0
            pipe_parts.append("semantic")

    # Pre-rerank debug
    for i, doc in enumerate(docs, 1):
        d = _doc_snippet(doc)
        d["id"] = i; d["score"] = None
        debug["pre_rerank_docs"].append(d)

    # Step 2: Reranking (optional)
    if use_rerank:
        t0 = time.perf_counter()
        from sentence_transformers import CrossEncoder

        @lru_cache(maxsize=1)
        def _reranker():
            return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

        reranker = _reranker()
        pairs = [(search_query, doc.page_content) for doc in docs]
        scores = reranker.predict(pairs)
        ranked = sorted(zip(docs, scores), key=lambda x: float(x[1]), reverse=True)

        # Update pre-rerank with scores
        for i, (doc, score) in enumerate(zip(docs, scores)):
            if i < len(debug["pre_rerank_docs"]):
                debug["pre_rerank_docs"][i]["score"] = float(score)

        docs = [doc for doc, _ in ranked[:5]]
        for i, (doc, score) in enumerate(ranked[:5], 1):
            d = _doc_snippet(doc)
            d["id"] = i; d["score"] = float(score)
            debug["post_rerank_docs"].append(d)

        debug["timing"]["rerank"] = time.perf_counter() - t0
        pipe_parts.append("rerank")

    # Step 3: Self-RAG (optional)
    if use_selfrag:
        t0 = time.perf_counter()
        from src.application.chain_selfrag import (
            _build_context_and_sources, _answer_with_context,
            _extract_json_payload,
        )
        from src.application.prompts import get_self_rag_eval_prompt, get_self_rag_rewrite_prompt
        from langchain_community.llms import Ollama

        llm = Ollama(model="qwen2.5:7b", temperature=0.3, top_p=0.9, repeat_penalty=1.1)
        context_str, sources = _build_context_and_sources(docs)
        answer = _answer_with_context(llm, query, context_str, ctx) # use original query for answering

        eval_raw = llm.invoke(get_self_rag_eval_prompt().format(
            question=query, context=context_str, answer=answer))
        payload = _extract_json_payload(eval_raw)
        confidence = max(0.0, min(1.0, float(payload.get("confidence", 0.5))))
        needs_rewrite = bool(payload.get("needs_rewrite", False))
        rewritten = str(payload.get("rewritten_query", "")).strip()

        debug["confidence"] = confidence
        debug["hops_used"] = 1

        if needs_rewrite or confidence < 0.62:
            debug["hops_used"] = 2
            if not rewritten:
                from src.application.chain_selfrag import _format_chat_history
                rewritten = str(llm.invoke(get_self_rag_rewrite_prompt().format(
                    question=query, chat_history=_format_chat_history(ctx)))).strip()
            debug["rewritten_query_hop2"] = rewritten
            if rewritten:
                if search_mode == "hybrid":
                    from src.data_layer.vector_store import create_hybrid_retriever_from_vector_store
                    docs2 = create_hybrid_retriever_from_vector_store(vdb, k=5).invoke(rewritten)
                else:
                    docs2 = vdb.as_retriever(search_kwargs={"k": 5}).invoke(rewritten)
                if docs2:
                    ctx2, src2 = _build_context_and_sources(docs2)
                    ans2 = _answer_with_context(llm, rewritten, ctx2, ctx)
                    answer = llm.invoke(
                        f"Tổng hợp:\nCÂU HỎI: {query}\n"
                        f"HOP 1: {answer}\nHOP 2 (rewrite: {rewritten}): {ans2}\n"
                        f"Trả lời dựa trên cả 2 hop, trích dẫn [Nguồn X].")
                    sources = sources + src2
                    for i, s in enumerate(sources, 1):
                        s["id"] = i
                    confidence = 0.7

        answer_text = (f"{answer}\n\n(Self-RAG: {debug['hops_used']} hop · "
                       f"confidence: {confidence:.0%})")
        if debug.get("rewritten_query_hop2"):
            answer_text += f"\nQuery rewrite (hop 2): {debug['rewritten_query_hop2']}"
            
        debug["timing"]["selfrag"] = time.perf_counter() - t0
        pipe_parts.append("self-rag")
        debug["pipeline"] = " → ".join(pipe_parts)
        debug["timing"]["total"] = time.perf_counter() - t_total
        return answer_text, sources, debug

    # No self-rag — need LLM call with retrieved docs
    t0 = time.perf_counter()
    from src.application.chain_selfrag import _build_context_and_sources, _answer_with_context
    from langchain_community.llms import Ollama
    llm = Ollama(model="qwen2.5:7b", temperature=0.7, top_p=0.9, repeat_penalty=1.1)
    context_str, sources = _build_context_and_sources(docs)
    response = _answer_with_context(llm, query, context_str, ctx) # use original query for answering
    debug["timing"]["llm"] = time.perf_counter() - t0
    pipe_parts.append("llm")
    debug["pipeline"] = " → ".join(pipe_parts)
    debug["timing"]["total"] = time.perf_counter() - t_total
    return response, sources, debug

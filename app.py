import streamlit as st
import hashlib, importlib, time
from pathlib import Path
from functools import lru_cache

from data.history import (
    add_message, clear_all, clear_vector_store_directory,
    delete_conversation, get_conversation, load_conversations, new_conversation,
)
from src.application.chain_citation import get_answer_with_citation
from src.application.chain_hybrid import get_answer_with_hybrid_citation
from src.application.chain_multidoc import get_answer_multidoc
from src.application.pipeline import process_pdf_to_vectorstore, process_multiple_pdfs_to_vectorstore
from src.presentation.comp_citation import render_answer as render_citation, render_comparison
from src.presentation.comp_multidoc import render_doc_filter
from src.presentation.components import (
    render_collapsed_sidebar_toggle, render_header, render_status_bar,
    render_chat_messages, render_qa_input, render_sidebar, render_debug_panel,
)
from src.presentation.styles import get_css

st.set_page_config(page_title="SmartDoc AI", page_icon="📄", layout="wide", initial_sidebar_state="expanded")

# ── Helpers ──────────────────────────────────────────────────────────
def normalize_sources(raw) -> list[dict]:
    out = []
    for i, s in enumerate(raw or [], 1):
        if isinstance(s, dict):
            out.append({"id": s.get("id", i), "page": s.get("page", "?"),
                         "content": str(s.get("content", "")).strip(),
                         "source_file": s.get("source_file", "Tài liệu")})
        else:
            txt = str(s).strip(); sf, pg = "Tài liệu", "?"
            if " - Trang " in txt:
                sf, _, pg = txt.partition(" - Trang ")
                sf = sf.strip() or "Tài liệu"; pg = pg.strip() or "?"
            out.append({"id": i, "page": pg, "content": txt, "source_file": sf})
    return out

def build_source_text(sources: list[dict]) -> str:
    labels = []
    for s in sources:
        sf = str(s.get("source_file", "Tài liệu")).strip() or "Tài liệu"
        pg = s.get("page")
        labels.append(f"{sf} — Trang {pg}" if pg not in (None, "", "?") else sf)
    return "Nguồn: " + (", ".join(dict.fromkeys(labels)) or "N/A")

def _doc_snippet(doc, max_len=120) -> dict:
    """Build a debug-friendly doc dict."""
    meta = doc.metadata or {}
    raw_page = meta.get("page", 0)
    page = raw_page + 1 if isinstance(raw_page, int) else (raw_page or "?")
    fname = str(meta.get("filename") or meta.get("source") or "?").split("/")[-1]
    text = (doc.page_content or "")[:max_len].replace("\n", " ")
    return {"file": fname, "page": page, "snippet": text}

# ── State ────────────────────────────────────────────────────────────
for k, v in {"dark_mode": False, "sidebar_collapsed": False,
             "answer": None, "processing_step": 0, "vector_db": None,
             "uploaded_signature": None, "active_conversation_id": None,
             "chunk_size": 1000, "chunk_overlap": 150,
             "search_mode": "semantic", "use_rerank": False, "use_selfrag": False,
             "last_query_fingerprint": None, "benchmark_log": [],
             "file_count": 0, "debug_info": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.markdown(get_css(dark_mode=st.session_state.dark_mode,
                     sidebar_collapsed=st.session_state.sidebar_collapsed), unsafe_allow_html=True)

MAX_MB = 25

# ── Sidebar ──────────────────────────────────────────────────────────
hist = load_conversations()
hist_map = {c["id"]: c for c in hist if c.get("id")}

if st.session_state.sidebar_collapsed:
    sb = dict(conv=None, delete=None, new=False, toggle=False,
              clr_hist=False, clr_vec=False, cs=st.session_state.chunk_size,
              co=st.session_state.chunk_overlap, search_mode=st.session_state.search_mode,
              use_rerank=st.session_state.use_rerank, use_selfrag=st.session_state.use_selfrag,
              files=None)
    sb["toggle"] = render_collapsed_sidebar_toggle()
else:
    sb = render_sidebar(
        chat_history=hist, active_conversation_id=st.session_state.active_conversation_id,
        dark_mode=st.session_state.dark_mode, chunk_size=st.session_state.chunk_size,
        chunk_overlap=st.session_state.chunk_overlap, search_mode=st.session_state.search_mode,
        use_rerank=st.session_state.use_rerank, use_selfrag=st.session_state.use_selfrag,
    )

st.session_state.chunk_size = sb["cs"]
st.session_state.chunk_overlap = sb["co"]
st.session_state.search_mode = sb["search_mode"]
st.session_state.use_rerank = sb["use_rerank"]
st.session_state.use_selfrag = sb["use_selfrag"]
files = sb["files"]

# ── Sidebar actions ──────────────────────────────────────────────────
if sb["toggle"]:
    st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed; st.rerun()
if sb["clr_hist"]:
    clear_all(); st.session_state.active_conversation_id = None; st.session_state.answer = None
    st.session_state.debug_info = None; st.toast("Đã xóa lịch sử."); st.rerun()
if sb["clr_vec"]:
    if clear_vector_store_directory():
        st.session_state.vector_db = None; st.session_state.uploaded_signature = None
        st.session_state.processing_step = 0; st.session_state.file_count = 0
        st.session_state.debug_info = None; st.toast("Đã xóa Vector Store."); st.rerun()
    else:
        st.error("Không thể xóa Vector Store.")
if sb["delete"]:
    if delete_conversation(sb["delete"]):
        if st.session_state.active_conversation_id == sb["delete"]:
            st.session_state.active_conversation_id = None; st.session_state.answer = None
        st.rerun()
if sb["new"]:
    st.session_state.active_conversation_id = None; st.session_state.answer = None
    st.session_state.question_input = ""; st.session_state.last_query_fingerprint = None
    st.session_state.debug_info = None; st.rerun()
if sb["conv"]:
    st.session_state.active_conversation_id = sb["conv"]
    c = hist_map.get(sb["conv"])
    if c and c.get("messages"):
        last = c["messages"][-1]
        st.session_state.answer = {"text": last.get("answer", ""), "source": last.get("source", ""),
                                    "sources": normalize_sources(last.get("sources", [])),
                                    "query": last.get("question", "")}
        st.session_state.question_input = last.get("question", "")
    else:
        st.session_state.answer = None; st.session_state.question_input = ""
    st.session_state.debug_info = None; st.rerun()

# ── Header + status ──────────────────────────────────────────────────
dm = render_header(dark_mode=st.session_state.dark_mode)
if dm != st.session_state.dark_mode:
    st.session_state.dark_mode = dm; st.rerun()

render_status_bar(st.session_state.vector_db, st.session_state.processing_step,
                  st.session_state.file_count, st.session_state.search_mode,
                  st.session_state.use_rerank, st.session_state.use_selfrag)

# ── Upload ───────────────────────────────────────────────────────────
if files:
    valid = [f for f in files if f.size <= MAX_MB * 1024 * 1024]
    for f in files:
        if f not in valid:
            st.error(f"{f.name} vượt quá {MAX_MB} MB.")
    if valid:
        sig = "|".join(sorted(f"{f.name}:{hashlib.md5(f.getvalue()).hexdigest()}" for f in valid))
        sig += f":{sb['cs']}:{sb['co']}"
        if sig != st.session_state.uploaded_signature:
            try:
                pdf_dir = Path("data/pdfs"); pdf_dir.mkdir(parents=True, exist_ok=True)
                idx_dir = Path("data/faiss_index") / hashlib.md5(sig.encode()).hexdigest()
                idx_dir.parent.mkdir(parents=True, exist_ok=True)
                paths = []
                for f in valid:
                    p = pdf_dir / Path(f.name).name; p.write_bytes(f.getvalue()); paths.append(str(p))
                st.session_state.processing_step = 2
                with st.spinner(f"Đang xử lý {len(paths)} tài liệu..."):
                    if len(paths) == 1:
                        vdb, stats = process_pdf_to_vectorstore(paths[0], str(idx_dir), sb["cs"], sb["co"], return_stats=True)
                    else:
                        vdb, stats = process_multiple_pdfs_to_vectorstore(paths, str(idx_dir), sb["cs"], sb["co"])
                st.session_state.vector_db = vdb
                st.session_state.processing_step = 3
                st.session_state.uploaded_signature = sig
                st.session_state.file_count = len(paths)
                st.session_state.benchmark_log.append({
                    "benchmark_type": "chunk", "chunk_size": stats.get("chunk_size"),
                    "chunk_overlap": stats.get("chunk_overlap"), "chunks": stats.get("chunk_count"),
                    "time": stats.get("total_time_sec"),
                })
                st.toast(f"Upload xong: {len(paths)} file, {stats.get('chunk_count', '?')} chunks")
                st.rerun()
            except Exception as exc:
                st.session_state.processing_step = 0; st.session_state.vector_db = None
                st.error(f"Lỗi xử lý: {exc}")

# ── Doc filter ───────────────────────────────────────────────────────
meta_filter = None
if st.session_state.vector_db is not None and st.session_state.file_count > 1:
    with st.expander("Bộ lọc tài liệu", expanded=False):
        meta_filter = render_doc_filter(st.session_state.vector_db)

# ── Chat history ─────────────────────────────────────────────────────
if st.session_state.active_conversation_id:
    conv = get_conversation(st.session_state.active_conversation_id)
    msgs = conv.get("messages", []) if conv else []
    if msgs:
        render_chat_messages(msgs)

# ── Input ────────────────────────────────────────────────────────────
question, send_clicked, compare_clicked = render_qa_input()

# ── RAG pipeline ─────────────────────────────────────────────────────
def run_pipeline(query, vdb, ctx, search_mode, use_rerank, use_selfrag, meta_filter=None):
    """Composable pipeline: search → (rerank) → (self-rag) → LLM."""
    debug = {"pipeline": "", "timing": {}, "pre_rerank_docs": [], "post_rerank_docs": []}
    pipe_parts = []

    t_total = time.perf_counter()

    # Step 1: Retrieval
    if meta_filter:
        t0 = time.perf_counter()
        response, raw_sources = get_answer_multidoc(query, vdb, metadata_filter=meta_filter)
        debug["timing"]["multidoc"] = time.perf_counter() - t0
        pipe_parts.append("multidoc")
        debug["pipeline"] = " → ".join(pipe_parts)
        debug["timing"]["total"] = time.perf_counter() - t_total
        return response, raw_sources, debug

    if search_mode == "hybrid":
        t0 = time.perf_counter()
        if not use_rerank and not use_selfrag:
            response, raw_sources = get_answer_with_hybrid_citation(query, vdb, chat_history=ctx)
            debug["timing"]["hybrid_search+llm"] = time.perf_counter() - t0
            pipe_parts.append("hybrid")
            debug["pipeline"] = " → ".join(pipe_parts)
            debug["timing"]["total"] = time.perf_counter() - t_total
            return response, raw_sources, debug
        else:
            # Need raw docs for rerank/selfrag — use hybrid retriever only
            from src.data_layer.vector_store import create_hybrid_retriever_from_vector_store
            retriever = create_hybrid_retriever_from_vector_store(vdb, k=12 if use_rerank else 5)
            docs = retriever.invoke(query)
            debug["timing"]["hybrid_retrieve"] = time.perf_counter() - t0
            pipe_parts.append("hybrid")
    else:
        t0 = time.perf_counter()
        if not use_rerank and not use_selfrag:
            response, raw_sources = get_answer_with_citation(query, vdb, chat_history=ctx)
            debug["timing"]["semantic_search+llm"] = time.perf_counter() - t0
            pipe_parts.append("semantic")
            debug["pipeline"] = " → ".join(pipe_parts)
            debug["timing"]["total"] = time.perf_counter() - t_total
            return response, raw_sources, debug
        else:
            retriever = vdb.as_retriever(search_type="similarity",
                                          search_kwargs={"k": 12 if use_rerank else 5, "fetch_k": 20})
            docs = retriever.invoke(query)
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
        pairs = [(query, doc.page_content) for doc in docs]
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
        from src.application.promts import get_self_rag_eval_prompt, get_self_rag_rewrite_prompt
        from langchain_community.llms import Ollama

        llm = Ollama(model="qwen2.5:7b", temperature=0.3, top_p=0.9, repeat_penalty=1.1)
        context_str, sources = _build_context_and_sources(docs)
        answer = _answer_with_context(llm, query, context_str, ctx)

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
            debug["rewritten_query"] = rewritten
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
        if debug.get("rewritten_query"):
            answer_text += f"\nQuery rewrite: {debug['rewritten_query']}"
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
    response = _answer_with_context(llm, query, context_str, ctx)
    debug["timing"]["llm"] = time.perf_counter() - t0
    pipe_parts.append("llm")
    debug["pipeline"] = " → ".join(pipe_parts)
    debug["timing"]["total"] = time.perf_counter() - t_total
    return response, sources, debug


# ── Execute query ────────────────────────────────────────────────────
if send_clicked or compare_clicked:
    fp = (question.strip(), str(compare_clicked), st.session_state.search_mode,
          st.session_state.use_rerank, st.session_state.use_selfrag, str(meta_filter))

    if not question:
        st.warning("Nhập câu hỏi trước.")
    elif st.session_state.vector_db is None:
        st.warning("Upload PDF trước.")
    elif fp == st.session_state.last_query_fingerprint:
        st.info("Câu hỏi đã xử lý. Thay đổi pipeline hoặc hỏi câu khác.")
    else:
        try:
            actv = get_conversation(st.session_state.active_conversation_id)
            ctx = actv.get("messages", []) if actv else []
            graph_cmp = None

            with st.spinner("Đang phân tích..."):
                if compare_clicked:
                    # RAG vs GraphRAG comparison
                    t0 = time.perf_counter()
                    vr, vs, vdbg = run_pipeline(question, st.session_state.vector_db, ctx,
                                                 st.session_state.search_mode,
                                                 st.session_state.use_rerank,
                                                 st.session_state.use_selfrag)
                    vt = time.perf_counter() - t0
                    gm = importlib.import_module("src.application.chain_graphrag")
                    t0 = time.perf_counter()
                    gr, gs, gst = gm.get_answer_with_graphrag_citation(question, st.session_state.vector_db, chat_history=ctx)
                    gt = time.perf_counter() - t0
                    vsn = normalize_sources(vs); gsn = normalize_sources(gs)
                    olap = len(set((s["source_file"], s["page"]) for s in vsn) & set((s["source_file"], s["page"]) for s in gsn))
                    graph_cmp = {
                        "query": question,
                        "vector": {"text": vr, "source": build_source_text(vsn), "sources": vsn, "query": question, "time": round(vt, 2)},
                        "graphrag": {"text": gr, "source": build_source_text(gsn), "sources": gsn, "query": question, "time": round(gt, 2)},
                        "overlap": olap,
                    }
                    response, raw_sources, debug = vr, vs, vdbg
                else:
                    response, raw_sources, debug = run_pipeline(
                        question, st.session_state.vector_db, ctx,
                        st.session_state.search_mode, st.session_state.use_rerank,
                        st.session_state.use_selfrag, meta_filter=meta_filter)

            sources = normalize_sources(raw_sources)
            src_text = build_source_text(sources)

            if not compare_clicked:
                cid = st.session_state.active_conversation_id
                if not cid:
                    dn = ", ".join(f.name for f in (files or []))
                    cid = new_conversation(doc_name=dn)["id"]
                    st.session_state.active_conversation_id = cid
                if add_message(cid, question, response, src_text) is None:
                    cid = new_conversation(doc_name="")["id"]
                    st.session_state.active_conversation_id = cid
                    add_message(cid, question, response, src_text)

            st.session_state.answer = {
                "text": response, "source": src_text, "sources": sources, "query": question,
                "graph_comparison": graph_cmp,
            }
            st.session_state.debug_info = debug
            st.session_state.last_query_fingerprint = fp
            st.rerun()
        except Exception as exc:
            st.error(f"Lỗi RAG: {exc}")

# ── Render answer ────────────────────────────────────────────────────
if st.session_state.answer:
    ap = st.session_state.answer
    gc = ap.get("graph_comparison")

    if gc:
        st.markdown('<div class="compare-header">RAG vs GraphRAG</div>', unsafe_allow_html=True)
        stats = (f"Overlap: {gc.get('overlap', 0)} nguồn chung · "
                 f"RAG: {gc['vector'].get('time', '?')}s · "
                 f"GraphRAG: {gc['graphrag'].get('time', '?')}s")
        render_comparison("RAG", gc["vector"], "GraphRAG", gc["graphrag"], stats_text=stats)
    else:
        with st.chat_message("assistant"):
            render_citation(ap, key_prefix="main")

# ── Debug panel ──────────────────────────────────────────────────────
render_debug_panel(st.session_state.debug_info)

# ── Benchmark ────────────────────────────────────────────────────────
with st.expander("Benchmark", expanded=False):
    logs = st.session_state.get("benchmark_log", [])
    if not logs:
        st.caption("Chưa có dữ liệu.")
    else:
        st.dataframe(logs[-10:], use_container_width=True)

import streamlit as st
import hashlib, time
from pathlib import Path

from data.history import (
    add_message, clear_all, clear_vector_store_directory,
    delete_conversation, get_conversation, load_conversations, new_conversation,
)
from src.application.pipeline import process_multiple_files_to_vectorstore, get_embeddings
from src.application.query_handler import (
    handle_standard_query, handle_comparison_query, create_benchmark_log_entry
)
from src.data_layer.vector_store import load_if_exists
from src.presentation.comp_citation import render_answer as render_citation, render_comparison
from src.presentation.comp_multidoc import render_doc_filter
from src.presentation.comp_graph import render_graph_from_vector_store, get_graph_stats
from src.presentation.components import (
    render_collapsed_sidebar_toggle, render_header, render_status_bar,
    render_chat_messages, render_sidebar, render_debug_panel,
)
from src.presentation.styles import get_css
from src.utils.doc_helpers import normalize_sources, build_source_text

st.set_page_config(page_title="SmartDoc AI", page_icon="📄", layout="wide", initial_sidebar_state="expanded")

# Warm up cached resources ngay khi app start — tránh delay ở lần query đầu tiên
from src.model_layer.cache import get_cached_embedder, get_cached_llm
get_cached_embedder()
get_cached_llm(temperature=0.7)
get_cached_llm(temperature=0.1)
get_cached_llm(temperature=0.3)

# ── State ────────────────────────────────────────────────────────────
for k, v in {"dark_mode": False, "sidebar_collapsed": False,
             "answer": None, "processing_step": 0, "vector_db": None,
             "uploaded_signature": None, "active_conversation_id": None,
             "chunk_size": 500, "chunk_overlap": 100,  # Optimized: 1000→500, 150→100
             "search_mode": "semantic", "use_rerank": False, "use_selfrag": False,
             "last_query_fingerprint": None, "benchmark_log": [],
             "file_count": 0, "debug_info": None,
             "processed_files": {}, "chunk_count": 0}.items():
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
              files=None, show_graph=False)
    sb["toggle"] = render_collapsed_sidebar_toggle()
else:
    # Tính index_status và graph_stats để truyền vào sidebar
    _vdb = st.session_state.vector_db
    _step = st.session_state.processing_step
    _index_status = "cached" if _vdb is not None else ("processing" if _step == 2 else "none")
    _graph_stats = get_graph_stats(_vdb) if _vdb is not None else {"nodes": 0, "edges": 0}

    sb = render_sidebar(
        chat_history=hist, active_conversation_id=st.session_state.active_conversation_id,
        dark_mode=st.session_state.dark_mode, chunk_size=st.session_state.chunk_size,
        chunk_overlap=st.session_state.chunk_overlap, search_mode=st.session_state.search_mode,
        use_rerank=st.session_state.use_rerank, use_selfrag=st.session_state.use_selfrag,
        index_status=_index_status,
        chunk_count=st.session_state.chunk_count,
        graph_stats=_graph_stats,
    )

st.session_state.chunk_size = sb["cs"]
st.session_state.chunk_overlap = sb["co"]
st.session_state.search_mode = sb["search_mode"]
st.session_state.use_rerank = sb["use_rerank"]
st.session_state.use_selfrag = sb["use_selfrag"]

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
        st.session_state.debug_info = None; st.session_state.processed_files = {}
        st.toast("Đã xóa Vector Store."); st.rerun()
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
                  st.session_state.file_count)

# ── Upload ───────────────────────────────────────────────────────────
if not st.session_state.vector_db:
    st.markdown('<div style="text-align: center; margin: 4rem 0; padding: 2rem; border: 2px dashed #10A37F; border-radius: 1rem; background: rgba(16,163,127,0.05);">', unsafe_allow_html=True)
    st.markdown("### 📄 Kéo thả tài liệu để kích hoạt SmartDoc AI")
    files = st.file_uploader("Upload", type=["pdf", "docx"], accept_multiple_files=True, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    with st.expander("📄 Quản lý tài liệu", expanded=False):
        files = st.file_uploader("Upload", type=["pdf", "docx"], accept_multiple_files=True, label_visibility="collapsed")
    if files:
        st.success(f"✅ Đã tải lên tài liệu: {', '.join(f.name for f in files)}")

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
                pdf_dir = Path("data/documents"); pdf_dir.mkdir(parents=True, exist_ok=True)
                idx_dir = Path("data/faiss_index") / hashlib.md5(sig.encode()).hexdigest()
                idx_dir.parent.mkdir(parents=True, exist_ok=True)

                # Kiểm tra cache: nếu index đã tồn tại trên disk thì load lại,
                # không cần chunking + embedding lại từ đầu
                cached_vdb = load_if_exists(str(idx_dir), get_embeddings())
                if cached_vdb is not None:
                    st.session_state.vector_db = cached_vdb
                    st.session_state.processing_step = 3
                    st.session_state.uploaded_signature = sig
                    st.session_state.file_count = len(valid)
                    st.session_state.processed_files[sig] = str(idx_dir)
                    st.toast(f"Đã tải index từ cache: {len(valid)} file")
                    st.rerun()
                else:
                    # Lần đầu xử lý: lưu file lên disk rồi build index mới
                    paths = []
                    for f in valid:
                        p = pdf_dir / Path(f.name).name; p.write_bytes(f.getvalue()); paths.append(str(p))
                    st.session_state.processing_step = 2
                    with st.spinner("Đang xử lý tài liệu..."):
                        vdb, stats = process_multiple_files_to_vectorstore(paths, str(idx_dir), sb["cs"], sb["co"])
                    st.session_state.vector_db = vdb
                    st.session_state.processing_step = 3
                    st.session_state.uploaded_signature = sig
                    st.session_state.file_count = len(paths)
                    st.session_state.chunk_count = stats.get("chunk_count", 0)
                    st.session_state.processed_files[sig] = str(idx_dir)
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

# ── Knowledge Graph ───────────────────────────────────────────────────
if sb.get("show_graph") and st.session_state.vector_db is not None:
    with st.expander("🕸️ Knowledge Graph", expanded=True):
        render_graph_from_vector_store(st.session_state.vector_db, height="480px")

# ── Chat history ─────────────────────────────────────────────────────
if st.session_state.active_conversation_id:
    conv = get_conversation(st.session_state.active_conversation_id)
    msgs = conv.get("messages", []) if conv else []
    if msgs:
        render_chat_messages(msgs)

# ── Input ────────────────────────────────────────────────────────────
# Use columns for input + buttons
col_input, col_submit, col_compare = st.columns([6, 1, 1])

with col_input:
    question = st.text_input(
        "Nhập câu hỏi về tài liệu...",
        key="question_input_field",
        label_visibility="collapsed",
        placeholder="Nhập câu hỏi về tài liệu..."
    )

with col_submit:
    send_clicked = st.button("📤 Gửi", use_container_width=True, type="primary")

with col_compare:
    compare_clicked = st.button("⚡ Compare", use_container_width=True, help="So sánh RAG vs GraphRAG")

# Store question for later use
if send_clicked or compare_clicked:
    st.session_state.question_input = question



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

            with st.status("Đang xử lý...", expanded=True) as status:
                st.write("🔍 Đang tìm tài liệu...")
                if compare_clicked:
                    st.write("⚖️ Đang so sánh RAG vs GraphRAG...")
                    # Use query_handler for comparison
                    response, sources, src_text, debug, graph_cmp = handle_comparison_query(
                        question, st.session_state.vector_db, ctx,
                        st.session_state.search_mode,
                        st.session_state.use_rerank,
                        st.session_state.use_selfrag
                    )
                    
                    # Log benchmark
                    st.session_state.benchmark_log.append(create_benchmark_log_entry(
                        "compare",
                        question,
                        rag_time=graph_cmp["vector"]["time"],
                        graphrag_time=graph_cmp["graphrag"]["time"],
                        parallel_time=graph_cmp["parallel_time"],
                        time_saved=graph_cmp["vector"]["time"] + graph_cmp["graphrag"]["time"] - graph_cmp["parallel_time"],
                        rag_sources=len(sources),
                        graphrag_sources=len(graph_cmp["graphrag"]["sources"]),
                        overlap=graph_cmp["overlap"],
                    ))
                    
                    status.update(
                        label=f"✅ Đã phân tích {len(sources)} nguồn RAG & {len(graph_cmp['graphrag']['sources'])} nguồn GraphRAG",
                        state="complete",
                        expanded=False
                    )
                else:
                    st.write("🧠 Phân tích nội dung...")
                    # Use query_handler for standard query
                    response, sources, src_text, debug = handle_standard_query(
                        question, st.session_state.vector_db, ctx,
                        st.session_state.search_mode,
                        st.session_state.use_rerank,
                        st.session_state.use_selfrag,
                        meta_filter=meta_filter
                    )
                    status.update(label=f"✅ Tìm thấy {len(sources)} nguồn", state="complete", expanded=False)

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
                "debug_info": debug,  # Pass debug info to answer for rendering
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


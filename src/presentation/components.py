import streamlit as st
from html import escape


# ──────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────

def render_sidebar(
    chat_history: list[dict] | None = None,
    active_conversation_id: str | None = None,
    dark_mode: bool = False,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    search_mode: str = "semantic",
    use_rerank: bool = False,
    use_selfrag: bool = False,
) -> dict:
    """Sidebar with composable pipeline controls.

    Returns dict with keys:
        conv, delete, new, toggle, clr_hist, clr_vec,
        cs, co, search_mode, use_rerank, use_selfrag, files
    """
    out = dict(
        conv=None, delete=None, new=False, toggle=False,
        clr_hist=False, clr_vec=False,
        cs=chunk_size, co=chunk_overlap,
        search_mode=search_mode, use_rerank=use_rerank, use_selfrag=use_selfrag,
        files=None,
    )

    if "confirm_clear_history" not in st.session_state:
        st.session_state.confirm_clear_history = False
    if "confirm_clear_vector" not in st.session_state:
        st.session_state.confirm_clear_vector = False

    with st.sidebar:
        # Title
        col_t, col_c = st.columns([6, 1], gap="small")
        with col_t:
            st.markdown('<div class="sidebar-title">SmartDoc AI</div>', unsafe_allow_html=True)
        with col_c:
            if st.button("◀", key="collapse_sidebar_btn", type="tertiary"):
                out["toggle"] = True

        if st.button("Cuộc trò chuyện mới", use_container_width=True, key="new_chat_btn", type="primary"):
            out["new"] = True

        # ── Upload ──
        st.markdown('<div class="sidebar-section-label">Tài liệu</div>', unsafe_allow_html=True)
        out["files"] = st.file_uploader(
            "Upload PDF", type=["pdf"], accept_multiple_files=True,
            label_visibility="collapsed", key="pdf_uploader",
        )
        if out["files"]:
            st.caption(f"{len(out['files'])} file đã chọn")

        # ── Search mode (radio) ──
        st.markdown('<div class="sidebar-section-label">Search</div>', unsafe_allow_html=True)
        mode_idx = 0 if search_mode == "semantic" else 1
        sel_mode = st.radio(
            "Search mode", ["Semantic (FAISS)", "Hybrid (Semantic + BM25)"],
            index=mode_idx, key="search_mode_radio", label_visibility="collapsed",
        )
        out["search_mode"] = "semantic" if "Semantic" in sel_mode else "hybrid"

        # ── Post-retrieval toggles ──
        st.markdown('<div class="sidebar-section-label">Post-retrieval</div>', unsafe_allow_html=True)
        out["use_rerank"] = st.toggle("Reranking (Cross-Encoder)", value=use_rerank, key="toggle_rerank")
        out["use_selfrag"] = st.toggle("Self-RAG (evaluate + rewrite)", value=use_selfrag, key="toggle_selfrag")

        # ── Chunk config ──
        st.markdown('<div class="sidebar-section-label">Chunking</div>', unsafe_allow_html=True)
        out["cs"] = st.slider("Chunk size", 500, 2000, chunk_size, 100)
        out["co"] = st.slider("Overlap", 50, 300, chunk_overlap, 50)

        # ── Clear ──
        st.markdown('<div class="sidebar-section-label">Dọn dẹp</div>', unsafe_allow_html=True)

        if not st.session_state.confirm_clear_history:
            if st.button("Xóa lịch sử chat", key="btn_clr_hist", use_container_width=True):
                st.session_state.confirm_clear_history = True
                st.rerun()
        else:
            st.warning("Xóa toàn bộ lịch sử?")
            cy, cn = st.columns(2, gap="small")
            with cy:
                if st.button("Xóa", key="do_clr_hist", use_container_width=True, type="primary"):
                    out["clr_hist"] = True; st.session_state.confirm_clear_history = False
            with cn:
                if st.button("Hủy", key="no_clr_hist", use_container_width=True):
                    st.session_state.confirm_clear_history = False; st.rerun()

        if not st.session_state.confirm_clear_vector:
            if st.button("Xóa Vector Store", key="btn_clr_vec", use_container_width=True):
                st.session_state.confirm_clear_vector = True
                st.rerun()
        else:
            st.warning("Xóa Vector Store?")
            cy, cn = st.columns(2, gap="small")
            with cy:
                if st.button("Xóa", key="do_clr_vec", use_container_width=True, type="primary"):
                    out["clr_vec"] = True; st.session_state.confirm_clear_vector = False
            with cn:
                if st.button("Hủy", key="no_clr_vec", use_container_width=True):
                    st.session_state.confirm_clear_vector = False; st.rerun()

        # ── Chat history ──
        st.markdown('<div class="sidebar-section-label">Lịch sử</div>', unsafe_allow_html=True)
        convs = chat_history or []
        if not convs:
            st.markdown('<div class="empty-chat-chip">Chưa có hội thoại</div>', unsafe_allow_html=True)
        else:
            for conv in convs[:10]:
                cid = conv.get("id")
                if not cid:
                    continue
                title = (conv.get("title") or "Chat mới").replace("\n", " ").strip()
                if len(title) > 38:
                    title = title[:35] + "..."
                is_active = cid == active_conversation_id

                col_o, col_d = st.columns([8, 1], gap="small")
                with col_o:
                    btype = "primary" if is_active else "secondary"
                    if st.button(title, key=f"open_{cid}", use_container_width=True, type=btype):
                        out["conv"] = cid
                with col_d:
                    if st.button("✕", key=f"del_{cid}", type="tertiary", use_container_width=True):
                        out["delete"] = cid
                        break

    return out


def render_collapsed_sidebar_toggle() -> bool:
    col_l, _ = st.columns([1, 11])
    with col_l:
        return st.button("☰", key="expand_sidebar_btn", type="tertiary")


# ──────────────────────────────────────────────────────────────────────
# MAIN AREA
# ──────────────────────────────────────────────────────────────────────

def render_header(dark_mode: bool) -> bool:
    col_l, col_r = st.columns([8, 2])
    with col_l:
        st.markdown(
            '<div class="main-header"><h1>SmartDoc AI</h1>'
            '<p>Hỏi đáp thông minh từ tài liệu PDF</p></div>',
            unsafe_allow_html=True,
        )
    with col_r:
        light = st.toggle("Light", value=not dark_mode, key="theme_switch")
        return not light


def render_status_bar(vector_db, processing_step: int, file_count: int = 0,
                      search_mode: str = "semantic", use_rerank: bool = False, use_selfrag: bool = False):
    """Status bar showing pipeline config."""
    if processing_step == 2:
        dot, label = "processing", "Đang xử lý..."
    elif vector_db is not None:
        dot = "ready"
        pipeline_parts = [search_mode.title()]
        if use_rerank:
            pipeline_parts.append("Rerank")
        if use_selfrag:
            pipeline_parts.append("Self-RAG")
        pipe_str = " → ".join(pipeline_parts)
        label = f"Sẵn sàng · {file_count} file · {pipe_str}"
    else:
        dot, label = "pending", "Upload tài liệu để bắt đầu"

    st.markdown(
        f'<div class="status-bar"><span class="status-dot {dot}"></span> {label}</div>',
        unsafe_allow_html=True,
    )


def render_chat_messages(messages: list[dict]) -> None:
    if not messages:
        return
    for msg in messages:
        q = (msg.get("question") or "").strip()
        a = (msg.get("answer") or "").strip()
        source = (msg.get("source") or "").strip()
        if q:
            with st.chat_message("user"):
                st.markdown(q)
        if a:
            with st.chat_message("assistant"):
                st.markdown(a)
                if source:
                    st.caption(source)


def render_qa_input() -> tuple[str, bool, bool]:
    col_in, col_send, col_cmp = st.columns([5, 1, 1])
    with col_in:
        q = st.text_input(
            "q", placeholder="Nhập câu hỏi về tài liệu...",
            label_visibility="collapsed", key="question_input",
        )
    with col_send:
        send = st.button("Gửi", use_container_width=True, type="primary")
    with col_cmp:
        cmp = st.button("So sánh", use_container_width=True, type="secondary",
                         help="RAG vs GraphRAG side-by-side")
    return q, send, cmp


def render_debug_panel(debug_info: dict | None):
    """Render debug panel showing retrieved docs, rerank scores, query rewrite."""
    if not debug_info:
        return

    with st.expander("Debug Panel", expanded=False):
        # Pipeline info
        pipe = debug_info.get("pipeline", "")
        if pipe:
            st.markdown(f"**Pipeline:** `{pipe}`")

        # Query rewrite
        rewrite = debug_info.get("rewritten_query", "")
        if rewrite:
            st.markdown(f"**Query rewrite:** `{rewrite}`")

        # Self-RAG stats
        confidence = debug_info.get("confidence")
        hops = debug_info.get("hops_used")
        if confidence is not None:
            st.markdown(f"**Self-RAG:** {hops} hop(s) · confidence: {confidence:.0%}")

        # Retrieved docs — before rerank
        pre_docs = debug_info.get("pre_rerank_docs", [])
        if pre_docs:
            st.markdown("**Retrieved documents (before rerank):**")
            for d in pre_docs:
                score_str = f" · score: {d['score']:.4f}" if d.get("score") is not None else ""
                st.markdown(
                    f'<div class="debug-doc">'
                    f'<span class="debug-doc-label">[{d["id"]}] {d["file"]} p.{d["page"]}</span>'
                    f'{score_str}'
                    f'<div class="debug-doc-text">{d["snippet"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # After rerank
        post_docs = debug_info.get("post_rerank_docs", [])
        if post_docs:
            st.markdown("**After reranking:**")
            for d in post_docs:
                st.markdown(
                    f'<div class="debug-doc reranked">'
                    f'<span class="debug-doc-label">[{d["id"]}] {d["file"]} p.{d["page"]}</span>'
                    f' · score: {d["score"]:.4f}'
                    f'<div class="debug-doc-text">{d["snippet"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # Timing
        timing = debug_info.get("timing", {})
        if timing:
            st.markdown("**Timing:**")
            parts = [f"{k}: {v:.2f}s" for k, v in timing.items()]
            st.code(" | ".join(parts))
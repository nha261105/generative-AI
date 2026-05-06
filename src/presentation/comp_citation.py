import streamlit as st
import re

try:
    from st_copy_to_clipboard import st_copy_to_clipboard
except Exception:
    st_copy_to_clipboard = None


def _highlight(content: str, query: str) -> str:
    for w in query.split():
        if len(w) < 3:
            continue
        content = re.compile(f"({re.escape(w)})", re.IGNORECASE).sub(r"<mark>\1</mark>", content)
    return content


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\n", " ")).strip()


def _score_bar(score: float | None) -> str:
    """Render a mini HTML progress bar for relevance score."""
    if score is None:
        return '<span class="score-na">Score: N/A</span>'
    pct = max(0.0, min(1.0, float(score)))
    color = "#10A37F" if pct >= 0.6 else ("#F59E0B" if pct >= 0.35 else "#EF4444")
    return (
        f'<span class="score-label">Score: {pct:.3f}</span>'
        f'<span class="score-bar-wrap">'
        f'<span class="score-bar-fill" style="width:{pct*100:.1f}%;background:{color}"></span>'
        f'</span>'
    )


def render_answer(answer: dict, key_prefix: str = "default"):
    """Render answer text + expandable citation sources with score drill-down."""

    st.markdown(answer["text"])

    if st_copy_to_clipboard is not None:
        st_copy_to_clipboard(answer["text"], key=f"copy_{key_prefix}")

    # ── HIỂN THỊ PIPELINE BADGE ──
    debug_info = answer.get("debug_info")
    if debug_info:
        pipeline = debug_info.get("pipeline", "")
        if pipeline:
            badges = []
            if "hybrid" in pipeline:
                badges.append("🔀 Hybrid")
            elif "semantic" in pipeline:
                badges.append("🔍 Semantic")
            if "rerank" in pipeline:
                badges.append("🎯 Re-rank")
            if "self-rag" in pipeline:
                badges.append("🧠 Self-RAG")
            
            if badges:
                st.markdown(
                    f'<div style="margin: 0.5rem 0; padding: 0.5rem; background: rgba(16,163,127,0.1); '
                    f'border-radius: 0.5rem; font-size: 0.9rem;">'
                    f'<strong>Pipeline:</strong> {" + ".join(badges)}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        
        # ── HIỂN THỊ TIMING ──
        timing = debug_info.get("timing", {})
        if timing:
            total = timing.get("total", 0)
            timing_parts = [f"⏱️ **Tổng thời gian: {total:.2f}s**"]
            
            # Breakdown chi tiết
            breakdown = []
            if "hybrid_retrieve" in timing:
                breakdown.append(f"Retrieval: {timing['hybrid_retrieve']:.2f}s")
            elif "semantic_retrieve" in timing:
                breakdown.append(f"Retrieval: {timing['semantic_retrieve']:.2f}s")
            elif "hybrid_search+llm" in timing:
                breakdown.append(f"Hybrid+LLM: {timing['hybrid_search+llm']:.2f}s")
            elif "semantic_search+llm" in timing:
                breakdown.append(f"Semantic+LLM: {timing['semantic_search+llm']:.2f}s")
            
            if "rerank" in timing:
                breakdown.append(f"Re-rank: {timing['rerank']:.2f}s")
            if "selfrag" in timing:
                breakdown.append(f"Self-RAG: {timing['selfrag']:.2f}s")
            if "llm" in timing:
                breakdown.append(f"Generation: {timing['llm']:.2f}s")
            if "conv_rewrite" in timing:
                breakdown.append(f"Query rewrite: {timing['conv_rewrite']:.2f}s")
            
            if breakdown:
                timing_parts.append(f"({' · '.join(breakdown)})")
            
            st.caption(" ".join(timing_parts))

    sources = answer.get("sources") or []
    if not sources:
        return

    query = answer.get("query", "")

    # Source chips row
    chips_html = []
    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            continue
        sid = i + 1
        fname = src.get("source_file", "Tài liệu")
        page = src.get("page", "?")
        chips_html.append(
            f'<span class="source-chip">'
            f'<span class="sc-label">[{sid}]</span> '
            f'<span class="sc-file">{fname}</span> '
            f'<span class="sc-page">p.{page}</span>'
            f'</span>'
        )

    if chips_html:
        st.markdown(
            f'<div class="citation-header">Nguồn tham khảo</div>'
            f'<div>{"".join(chips_html)}</div>',
            unsafe_allow_html=True,
        )

    # Expandable drill-down per source
    with st.expander("🔍 Chi tiết trích dẫn", expanded=False):
        for i, src in enumerate(sources):
            if not isinstance(src, dict):
                continue
            sid = i + 1
            fname = src.get("source_file", "Tài liệu")
            page = src.get("page", "?")
            score = src.get("score")  # float hoặc None
            content = _clean(str(src.get("content", "")))
            highlighted = _highlight(content, query) if content else ""

            col1, col2, col3 = st.columns([4, 1, 1])
            col1.markdown(f"**Đoạn {sid}:** {content[:300]}{'...' if len(content) > 300 else ''}")
            col2.caption(f"📄 {fname}\np.{page}")
            score_display = f"{float(score):.3f}" if score is not None else "N/A"
            col3.caption(f"📊 Score\n{score_display}")

            if highlighted:
                st.markdown(
                    f'<div class="highlight-box">{highlighted}</div>',
                    unsafe_allow_html=True,
                )
            # Score bar
            st.markdown(
                f'<div class="score-row">{_score_bar(score)}</div>',
                unsafe_allow_html=True,
            )
            if i < len(sources) - 1:
                st.divider()


def render_comparison(
    left_label: str,
    left_answer: dict,
    right_label: str,
    right_answer: dict,
    stats_text: str = "",
):
    """Render side-by-side comparison (RAG vs GraphRAG)."""
    if stats_text:
        st.markdown(f'<div class="compare-stats">{stats_text}</div>', unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown(
            f'<div class="answer-card">'
            f'<div class="answer-badge">{left_label}</div>'
            f'<p class="answer-text">{left_answer.get("text", "")}</p>'
            f'<div class="answer-source">{left_answer.get("source", "")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        left_sources = left_answer.get("sources", [])
        if left_sources:
            with st.expander("🔍 Nguồn trích dẫn", expanded=False):
                for i, src in enumerate(left_sources):
                    if not isinstance(src, dict):
                        continue
                    fname = src.get("source_file", "Tài liệu")
                    page = src.get("page", "?")
                    score = src.get("score")
                    content = _clean(str(src.get("content", "")))
                    highlighted = _highlight(content, left_answer.get("query", "")) if content else ""
                    col1, col2, col3 = st.columns([4, 1, 1])
                    col1.markdown(f"**[{i+1}]** {content[:200]}{'...' if len(content) > 200 else ''}")
                    col2.caption(f"📄 {fname}\np.{page}")
                    col3.caption(f"📊 {float(score):.3f}" if score is not None else "📊 N/A")
                    if highlighted:
                        st.markdown(f'<div class="highlight-box">{highlighted}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="score-row">{_score_bar(score)}</div>', unsafe_allow_html=True)
                    if i < len(left_sources) - 1:
                        st.divider()

    with col_r:
        st.markdown(
            f'<div class="answer-card">'
            f'<div class="answer-badge">{right_label}</div>'
            f'<p class="answer-text">{right_answer.get("text", "")}</p>'
            f'<div class="answer-source">{right_answer.get("source", "")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        right_sources = right_answer.get("sources", [])
        if right_sources:
            with st.expander("🔍 Nguồn trích dẫn", expanded=False):
                for i, src in enumerate(right_sources):
                    if not isinstance(src, dict):
                        continue
                    fname = src.get("source_file", "Tài liệu")
                    page = src.get("page", "?")
                    score = src.get("score")
                    content = _clean(str(src.get("content", "")))
                    highlighted = _highlight(content, right_answer.get("query", "")) if content else ""
                    col1, col2, col3 = st.columns([4, 1, 1])
                    col1.markdown(f"**[{i+1}]** {content[:200]}{'...' if len(content) > 200 else ''}")
                    col2.caption(f"📄 {fname}\np.{page}")
                    col3.caption(f"📊 {float(score):.3f}" if score is not None else "📊 N/A")
                    if highlighted:
                        st.markdown(f'<div class="highlight-box">{highlighted}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="score-row">{_score_bar(score)}</div>', unsafe_allow_html=True)
                    if i < len(right_sources) - 1:
                        st.divider()

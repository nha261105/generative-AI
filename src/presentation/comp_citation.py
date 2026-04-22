import streamlit as st
import re

try:
    from st_copy_to_clipboard import st_copy_to_clipboard
except Exception:
    st_copy_to_clipboard = None


def _highlight(content: str, query: str) -> str:
    """Highlight query words (≥3 chars) in content with <mark> tags."""
    for w in query.split():
        if len(w) < 3:
            continue
        content = re.compile(f"({re.escape(w)})", re.IGNORECASE).sub(r"<mark>\1</mark>", content)
    return content


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\n", " ")).strip()


def render_answer(answer: dict, key_prefix: str = "default"):
    """Render answer text + expandable citation sources."""

    # Answer text inside chat-style container
    st.markdown(answer["text"])

    # Copy button
    if st_copy_to_clipboard is not None:
        st_copy_to_clipboard(answer["text"], key=f"copy_{key_prefix}")

    # Sources
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
            f'<div class="citation-header">Sources</div>'
            f'<div>{"".join(chips_html)}</div>',
            unsafe_allow_html=True,
        )

    # Expandable details
    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            continue
        sid = i + 1
        fname = src.get("source_file", "Tài liệu")
        page = src.get("page", "?")
        content = _clean(str(src.get("content", "")))
        highlighted = _highlight(content, query) if content else ""

        with st.expander(f"[{sid}] {fname} — Trang {page}"):
            if highlighted:
                st.markdown(
                    f'<div class="highlight-box">{highlighted}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption("Không có đoạn trích chi tiết.")


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
        # Left sources
        left_sources = left_answer.get("sources", [])
        if left_sources:
            for i, src in enumerate(left_sources):
                if not isinstance(src, dict):
                    continue
                fname = src.get("source_file", "Tài liệu")
                page = src.get("page", "?")
                content = _clean(str(src.get("content", "")))
                highlighted = _highlight(content, left_answer.get("query", "")) if content else ""
                with st.expander(f"[{i+1}] {fname} — p.{page}"):
                    if highlighted:
                        st.markdown(f'<div class="highlight-box">{highlighted}</div>', unsafe_allow_html=True)

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
            for i, src in enumerate(right_sources):
                if not isinstance(src, dict):
                    continue
                fname = src.get("source_file", "Tài liệu")
                page = src.get("page", "?")
                content = _clean(str(src.get("content", "")))
                highlighted = _highlight(content, right_answer.get("query", "")) if content else ""
                with st.expander(f"[{i+1}] {fname} — p.{page}"):
                    if highlighted:
                        st.markdown(f'<div class="highlight-box">{highlighted}</div>', unsafe_allow_html=True)

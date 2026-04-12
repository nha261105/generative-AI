import streamlit as st


def render_sidebar(
    chat_history: list[dict] | None = None,
    active_conversation_id: str | None = None,
) -> tuple[str | None, str | None]:
    """Render toàn bộ sidebar: logo, hướng dẫn, lịch sử chat, cấu hình hệ thống."""
    selected_conv_id = None
    deleted_conv_id = None

    with st.sidebar:
        # ── Logo ──────────────────────────────────────────────────────────────
        st.markdown('<div class="sidebar-title">SmartDoc AI 📄</div>', unsafe_allow_html=True)

        # ── Hướng dẫn sử dụng ────────────────────────────────────────────────
        st.markdown('<div class="sidebar-section-label">Hướng dẫn sử dụng</div>', unsafe_allow_html=True)
        steps = [
            ("Upload file PDF", False),
            ("Chờ hệ thống xử lý", False),
            ("Nhập câu hỏi", True),
            ("Nhận câu trả lời", False),
        ]
        for i, (label, active) in enumerate(steps, 1):
            badge_cls = "step-badge active" if active else "step-badge"
            text_cls  = "step-text active"  if active else "step-text"
            st.markdown(f"""
            <div class="step-item">
                <span class="{badge_cls}">{i}</span>
                <span class="{text_cls}">{label}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Lịch sử chat ─────────────────────────────────────────────────────
        st.markdown('<div class="sidebar-section-label">Lịch sử chat</div>', unsafe_allow_html=True)
        conversations = chat_history or []

        if not conversations:
            st.markdown(
                '<div class="config-chip">💬&nbsp; Chưa có hội thoại nào</div>',
                unsafe_allow_html=True,
            )
        else:
            for conv in conversations[:8]:
                conv_id = conv.get("id")
                if not conv_id:
                    continue

                title = (conv.get("title") or "Đoạn chat mới").replace("\n", " ").strip()
                doc_name = (conv.get("doc_name") or "").strip()
                message_count = len(conv.get("messages", []))
                suffix = f" · {message_count} lượt hỏi"

                if doc_name:
                    subtitle = f"📄 {doc_name}{suffix}"
                else:
                    subtitle = f"💬 Hội thoại{suffix}"

                col_open, col_delete = st.columns([5, 1], gap="small")
                with col_open:
                    open_type = "primary" if conv_id == active_conversation_id else "secondary"
                    if st.button(
                        f"💬 {title}",
                        key=f"open_conv_{conv_id}",
                        use_container_width=True,
                        type=open_type,
                    ):
                        selected_conv_id = conv_id
                    st.caption(subtitle)
                with col_delete:
                    if st.button(
                        "🗑️",
                        key=f"delete_conv_{conv_id}",
                        use_container_width=True,
                        help="Xóa hội thoại này",
                        type="tertiary",
                    ):
                        deleted_conv_id = conv_id
                        break

        # ── Cấu hình hệ thống ────────────────────────────────────────────────
        st.markdown('<div class="sidebar-footer">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section-label">Cấu hình hệ thống</div>', unsafe_allow_html=True)
        configs = [
            ("🧠", "Model: qwen2.5:7b"),
            ("🔗", "Embedding: mpnet"),
            ("🗄️", "Vector DB: FAISS"),
        ]
        for icon, label in configs:
            st.markdown(f'<div class="config-chip">{icon}&nbsp; {label}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    return selected_conv_id, deleted_conv_id


def render_header():
    """Render top header: tiêu đề app + avatar."""
    col_title, col_actions = st.columns([4, 1])
    with col_title:
        st.markdown("""
        <div class="main-header">
            <div>
                <h1>SmartDoc AI</h1>
                <p>Hỏi đáp thông minh từ tài liệu</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_actions:
        st.markdown("""
        <div style="display:flex;align-items:center;justify-content:flex-end;gap:0.75rem;padding-top:1.5rem;">
            <span style="font-size:1.25rem;cursor:pointer;color:#414754;">❓</span>
            <span style="font-size:1.25rem;cursor:pointer;color:#414754;">⚙️</span>
            <div class="avatar">AD</div>
        </div>
        """, unsafe_allow_html=True)


def render_upload_section() -> object:
    """
    Render khu vực upload PDF.

    Returns:
        uploaded_file: đối tượng file từ st.file_uploader (hoặc None).
    """
    uploaded_file = st.file_uploader(
        "Kéo thả file PDF vào đây",
        type=["pdf"],
        label_visibility="visible",
        key="pdf_uploader",
    )

    if uploaded_file is not None:
        size_mb = uploaded_file.size / (1024 * 1024)
        st.markdown(f"""
        <div class="file-chip">
            <span class="file-chip-icon">📕</span>
            <div>
                <div class="file-chip-name">{uploaded_file.name}</div>
                <div class="file-chip-size">{size_mb:.1f} MB</div>
            </div>
            <div class="file-chip-check">✓</div>
        </div>
        """, unsafe_allow_html=True)

    return uploaded_file


def render_pipeline(progress: int = 65):
    """
    Render thanh tiến trình xử lý tài liệu.

    Args:
        progress: phần trăm hoàn tất (0–100).
    """
    st.markdown(f"""
    <div class="pipeline-card">
        <div class="pipeline-label">
            <span>Trạng thái xử lý</span>
            <span>{progress}% Hoàn tất</span>
        </div>
        <div class="pipeline-bar-bg">
            <div class="pipeline-bar-fill" style="width:{progress}%"></div>
        </div>
        <div class="pipeline-steps">
            <div class="pipeline-step">
                <span style="color:#22C55E;font-size:1.1rem;">✅</span>
                <span class="label">Đọc tài liệu</span>
            </div>
            <div class="pipeline-step active">
                <div class="spinner"></div>
                <span class="label">Tạo embeddings</span>
            </div>
            <div class="pipeline-step pending">
                <span style="font-size:1.1rem;">⏳</span>
                <span class="label">Sẵn sàng</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_qa_section() -> tuple[str, bool]:
    """
    Render ô nhập câu hỏi và nút Gửi.

    Returns:
        (question, send_clicked): nội dung câu hỏi và trạng thái nút Gửi.
    """
    # st.markdown('<div class="qa-card">', unsafe_allow_html=True)
    st.markdown('<div class="qa-card-label">Đặt câu hỏi</div>', unsafe_allow_html=True)

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        question = st.text_input(
            "question",
            placeholder="Nhập câu hỏi của bạn về tài liệu này...",
            label_visibility="collapsed",
            key="question_input",
        )
    with col_btn:
        send_clicked = st.button("Gửi ➤", use_container_width=True, type="primary")

    st.markdown("</div>", unsafe_allow_html=True)
    return question, send_clicked


# def render_answer(answer: dict):
#     """
#     Render card hiển thị câu trả lời từ AI.

#     Args:
#         answer: dict với keys "text" và "source".
#     """
#     st.markdown(f"""
#     <div class="answer-card">
#         <div class="answer-badge">🤖 Trả lời</div>
#         <p class="answer-text">{answer["text"]}</p>
#         <div class="answer-source">📖 &nbsp;{answer["source"]}</div>
#         <div class="action-buttons">
#             <button class="action-btn">👍</button>
#             <button class="action-btn">👎</button>
#             <button class="action-btn">📋 Sao chép</button>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

def render_answer(vector_answer: dict, hybrid_answer: dict):
    """Render card hiển thị VECTOR và HYBRID answer"""

    st.markdown(f"""
    <div class="answer-card">
        <div class="answer-badge">🔎 Vector Search</div>
        <p class="answer-text">{vector_answer["text"]}</p>
        <div class="answer-source">📖 {vector_answer["source"]}</div>
    </div>
    """, unsafe_allow_html=True)


    st.markdown(f"""
    <div class="answer-card">
        <div class="answer-badge">⚡ Hybrid Search</div>
        <p class="answer-text">{hybrid_answer["text"]}</p>
        <div class="answer-source">📖 {hybrid_answer["source"]}</div>
    </div>
    """, unsafe_allow_html=True)


def render_status_fab():
    """Render floating status badge ở cuối trang."""
    st.markdown("""
    <div class="status-fab">
        <div class="pulse-dot"></div>
        Hệ thống đang hoạt động tốt &nbsp;→
    </div>
    """, unsafe_allow_html=True)
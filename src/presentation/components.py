import streamlit as st
from html import escape


def render_sidebar(
    chat_history: list[dict] | None = None,
    active_conversation_id: str | None = None,
    dark_mode: bool = False,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    retrieval_mode: str = "vector",
) -> tuple[str | None, str | None, bool, bool, bool, bool, int, int, str]:
    """Render sidebar tối giản kiểu ChatGPT: new chat + danh sách hội thoại."""
    selected_conv_id = None
    deleted_conv_id = None
    new_chat_clicked = False
    toggle_sidebar_clicked = False
    clear_history_clicked = False
    clear_vector_clicked = False
    selected_chunk_size = chunk_size
    selected_chunk_overlap = chunk_overlap
    selected_retrieval_mode = retrieval_mode

    with st.sidebar:
        col_title, col_toggle = st.columns([6, 1], gap="small")
        with col_title:
            st.markdown('<div class="sidebar-title">SmartDoc AI</div>', unsafe_allow_html=True)
        with col_toggle:
            if st.button("◀", key="collapse_sidebar_btn", type="tertiary"):
                toggle_sidebar_clicked = True

        if st.button("✚  Đoạn chat mới", use_container_width=True, key="new_chat_btn"):
            new_chat_clicked = True

        st.markdown('<div class="sidebar-section-label">Instructions</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="sidebar-panel">
                <div class="sidebar-panel-item">1. Upload file PDF</div>
                <div class="sidebar-panel-item">2. Doi he thong Embedding</div>
                <div class="sidebar-panel-item">3. Dat cau hoi va doc tra loi</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section-label">Model Configuration</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="sidebar-panel">
                <div class="sidebar-panel-item">LLM: qwen2.5:7b</div>
                <div class="sidebar-panel-item">Embedding: sentence-transformers</div>
                <div class="sidebar-panel-item">Vector store: FAISS</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section-label">Retrieval Mode</div>', unsafe_allow_html=True)
        mode_options = {
            "Vector Search": "vector",
            "Hybrid Search (Vector + BM25)": "hybrid",
        }
        selected_mode_label = st.selectbox(
            "Chế độ truy xuất",
            options=list(mode_options.keys()),
            index=0 if retrieval_mode == "vector" else 1,
            key="retrieval_mode_select",
            label_visibility="collapsed",
        )
        selected_retrieval_mode = mode_options[selected_mode_label]

        st.markdown('<div class="sidebar-section-label">Chunk Strategy</div>', unsafe_allow_html=True)
        selected_chunk_size = st.slider(
            "Chunk size",
            min_value=500,
            max_value=2000,
            value=chunk_size,
            step=100,
            help="Kích thước mỗi đoạn văn bản trước khi embedding",
        )
        selected_chunk_overlap = st.slider(
            "Chunk overlap",
            min_value=50,
            max_value=300,
            value=chunk_overlap,
            step=50,
            help="Số ký tự chồng lắp giữa các chunk",
        )

        st.markdown('<div class="sidebar-section-label">Clear Data</div>', unsafe_allow_html=True)
        with st.popover("Clear History"):
            st.warning("Thao tác này sẽ xóa toàn bộ lịch sử hội thoại.")
            confirm_history = st.checkbox(
                "Tôi xác nhận xóa toàn bộ lịch sử chat.",
                key="confirm_clear_history_check",
            )
            if st.button(
                "Xóa toàn bộ lịch sử",
                key="confirm_clear_history_btn",
                disabled=not confirm_history,
                use_container_width=True,
            ):
                clear_history_clicked = True

        with st.popover("Clear Vector Store"):
            st.warning("Thao tác này sẽ xóa toàn bộ tài liệu đã tải lên và chỉ mục FAISS.")
            confirm_vector = st.checkbox(
                "Tôi xác nhận xóa toàn bộ tài liệu đã upload.",
                key="confirm_clear_vector_check",
            )
            if st.button(
                "Xóa Vector Store",
                key="confirm_clear_vector_btn",
                disabled=not confirm_vector,
                use_container_width=True,
            ):
                clear_vector_clicked = True

        st.markdown('<div class="sidebar-section-label">Lịch sử đoạn chat</div>', unsafe_allow_html=True)
        conversations = chat_history or []

        if not conversations:
            st.markdown(
                '<div class="empty-chat-chip">Chưa có hội thoại nào</div>',
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
                    subtitle = f"{doc_name}{suffix}"
                else:
                    subtitle = f"Hội thoại{suffix}"

                col_open, col_menu = st.columns([8, 1], gap="small")
                with col_open:
                    open_type = "primary" if conv_id == active_conversation_id else "secondary"
                    if st.button(
                        title,
                        key=f"open_conv_{conv_id}",
                        use_container_width=True,
                        type=open_type,
                    ):
                        selected_conv_id = conv_id
                    st.caption(subtitle)
                with col_menu:
                    with st.popover("⋮"):
                        if st.button("Xóa đoạn chat", key=f"delete_conv_{conv_id}"):
                            deleted_conv_id = conv_id
                            break

    return (
        selected_conv_id,
        deleted_conv_id,
        new_chat_clicked,
        toggle_sidebar_clicked,
        clear_history_clicked,
        clear_vector_clicked,
        selected_chunk_size,
        selected_chunk_overlap,
        selected_retrieval_mode,
    )


def render_collapsed_sidebar_toggle() -> bool:
    """Render icon mở sidebar khi sidebar đang thu gọn."""
    col_left, _ = st.columns([1, 11])
    with col_left:
        return st.button("☰", key="expand_sidebar_btn", type="tertiary")


def render_header(dark_mode: bool) -> bool:
    """Render header với công tắc theme."""
    col_left, col_right = st.columns([6, 2])
    theme_selected = dark_mode

    with col_left:
        st.markdown("<div></div>", unsafe_allow_html=True)

    with col_right:
        light_mode = st.toggle("Light Mode", value=not dark_mode, key="theme_switch")
        theme_selected = not light_mode

    col_title, _ = st.columns([4, 1])
    with col_title:
        st.markdown("""
        <div class="main-header">
            <div>
                <h1>SmartDoc AI</h1>
                <p>Hỏi đáp thông minh từ tài liệu</p>
                <div class="quick-flow-wrap">
                    <div class="quick-flow-card">Upload file PDF</div>
                    <div class="quick-flow-sep">&gt;</div>
                    <div class="quick-flow-card">Đợi hệ thống Embedding</div>
                    <div class="quick-flow-sep">&gt;</div>
                    <div class="quick-flow-card">Đặt câu hỏi</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    return theme_selected


def render_processing_timeline(processing_step: int) -> None:
    """Render timeline 3 bước: Reading -> Embedding -> Ready."""
    steps = [(1, "Reading"), (2, "Embedding"), (3, "Ready")]
    cards = []
    for idx, label in steps:
        if processing_step <= 0:
            status = "pending"
        elif processing_step > idx:
            status = "done"
        elif processing_step == idx:
            status = "active"
        else:
            status = "pending"

        cards.append(f'<div class="timeline-card {status}">{label}</div>')
        if idx < len(steps):
            cards.append('<div class="timeline-sep">&gt;</div>')

    st.markdown(
        f'''
        <div class="timeline-wrap">
            <div class="timeline-title">Processing Timeline</div>
            <div class="timeline-cards">{"".join(cards)}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


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

def render_answer(vector_answer: dict, hybrid_answer: dict | None = None):
    """Render answer card for current vector mode and optional hybrid mode."""

    st.markdown(f"""
    <div class="answer-card">
        <div class="answer-badge">🔎 Vector Search</div>
        <p class="answer-text">{vector_answer["text"]}</p>
        <div class="answer-source">📖 {vector_answer["source"]}</div>
    </div>
    """, unsafe_allow_html=True)

    if hybrid_answer is not None:
        st.markdown(f"""
        <div class="answer-card">
            <div class="answer-badge">⚡ Hybrid Search</div>
            <p class="answer-text">{hybrid_answer["text"]}</p>
            <div class="answer-source">📖 {hybrid_answer["source"]}</div>
        </div>
        """, unsafe_allow_html=True)


def render_conversation_history(
    messages: list[dict],
    selected_index: int | None,
    key_prefix: str = "chat",
) -> int | None:
    """Render lịch sử câu hỏi trong đoạn chat và cho phép mở câu trả lời cũ."""
    if not messages:
        return selected_index

    st.markdown('<div class="chat-history-title">Lịch sử chat</div>', unsafe_allow_html=True)

    for idx, message in enumerate(messages):
        question = escape((message.get("question") or "").strip())
        if not question:
            continue

        col_q, col_expand = st.columns([12, 1])
        with col_q:
            st.markdown(
                f'<div class="chat-history-row">{question}</div>',
                unsafe_allow_html=True,
            )
        with col_expand:
            if st.button(
                ">",
                key=f"{key_prefix}_show_{idx}",
                type="tertiary",
                use_container_width=True,
            ):
                selected_index = None if selected_index == idx else idx

        if selected_index == idx:
            answer = escape((message.get("answer") or "").strip())
            source = escape((message.get("source") or "Nguồn: Không xác định").strip())
            st.markdown(
                f'''
                <div class="chat-history-answer">
                    <div class="chat-history-answer-text">{answer}</div>
                    <div class="chat-history-answer-source">{source}</div>
                </div>
                ''',
                unsafe_allow_html=True,
            )

    return selected_index
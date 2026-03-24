import streamlit as st


def render_sidebar():
    """Render toàn bộ sidebar: logo, hướng dẫn, điều hướng, cấu hình hệ thống."""
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

        # ── Điều hướng ───────────────────────────────────────────────────────
        st.markdown('<div class="sidebar-section-label">Điều hướng</div>', unsafe_allow_html=True)
        nav_items = [
            ("📤", "Tải tài liệu",       True),
            ("📊", "Phân tích nội dung", False),
            ("💬", "Đặt câu hỏi AI",     False),
            ("📄", "Trích xuất nguồn",   False),
        ]
        for icon, label, active in nav_items:
            cls = "nav-item active" if active else "nav-item"
            st.markdown(f'<div class="{cls}">{icon}&nbsp; {label}</div>', unsafe_allow_html=True)

        # ── Cấu hình hệ thống ────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
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
    st.markdown("""
    <div class="upload-dropzone">
        <div class="upload-icon-wrap">☁️</div>
        <h3>Kéo thả file PDF vào đây</h3>
        <p>hoặc nhấn để chọn file từ máy tính của bạn</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Chọn file PDF",
        type=["pdf"],
        label_visibility="collapsed",
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
    st.markdown('<div class="qa-card">', unsafe_allow_html=True)
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
        st.markdown("<br>", unsafe_allow_html=True)
        send_clicked = st.button("Gửi ➤", use_container_width=True, type="primary")

    st.markdown("</div>", unsafe_allow_html=True)
    return question, send_clicked


def render_answer(answer: dict):
    """
    Render card hiển thị câu trả lời từ AI.

    Args:
        answer: dict với keys "text" và "source".
    """
    st.markdown(f"""
    <div class="answer-card">
        <div class="answer-badge">🤖 Trả lời</div>
        <p class="answer-text">{answer["text"]}</p>
        <div class="answer-source">📖 &nbsp;{answer["source"]}</div>
        <div class="action-buttons">
            <button class="action-btn">👍</button>
            <button class="action-btn">👎</button>
            <button class="action-btn">📋 Sao chép</button>
        </div>
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
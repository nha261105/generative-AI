import streamlit as st

from src.presentation.styles import get_css
from src.presentation.components import (
    render_sidebar,
    render_header,
    render_upload_section,
    render_pipeline,
    render_qa_section,
    render_answer,
    render_status_fab,
)

# ─── Page config (phải đặt đầu tiên) ──────────────────────────────────────────
st.set_page_config(
    page_title="SmartDoc AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Inject CSS từ styles.py ───────────────────────────────────────────────────
st.markdown(get_css(), unsafe_allow_html=True)

# ─── Session state ─────────────────────────────────────────────────────────────
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "answer" not in st.session_state:
    st.session_state.answer = None
if "processing_step" not in st.session_state:
    st.session_state.processing_step = 1  # 1=reading, 2=embedding, 3=ready

# ─── Sidebar ───────────────────────────────────────────────────────────────────
render_sidebar()

# ─── Header ────────────────────────────────────────────────────────────────────
render_header()

# ─── Upload section ────────────────────────────────────────────────────────────
uploaded_file = render_upload_section()
if uploaded_file is not None:
    st.session_state.uploaded_file = uploaded_file

# ─── Processing pipeline ───────────────────────────────────────────────────────
render_pipeline(progress=65)

# ─── Q&A section ───────────────────────────────────────────────────────────────
question, send_clicked = render_qa_section()

if send_clicked and question:
    # TODO: thay bằng RAG pipeline thực tế
    st.session_state.answer = {
        "text": (
            "Dựa trên nội dung của tài liệu, mục tiêu chính của chương này là cung cấp cái nhìn "
            "tổng quan về các thuật toán học máy cơ bản. Tài liệu nhấn mạnh tầm quan trọng của "
            "việc làm sạch dữ liệu trước khi huấn luyện mô hình (trang 5) và đề cập rằng các mô "
            "hình tuyến tính thường là điểm bắt đầu tốt nhất cho người mới bắt đầu."
        ),
        "source": "Nguồn: trang 5, chương 2",
    }

if st.session_state.answer:
    render_answer(st.session_state.answer)

# ─── Status FAB ────────────────────────────────────────────────────────────────
render_status_fab()
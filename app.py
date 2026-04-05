import streamlit as st
import hashlib
from pathlib import Path

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
from src.application.pipeline import process_pdf_to_vectorstore
from src.application.rag_chain import get_answer

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
if "hybrid_answer" not in st.session_state:
    st.session_state.hybrid_answer = None
if "processing_step" not in st.session_state:
    st.session_state.processing_step = 1  # 1=reading, 2=embedding, 3=ready
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None
if "chunks" not in st.session_state:
    st.session_state.chunks = None
if "uploaded_signature" not in st.session_state:
    st.session_state.uploaded_signature = None
if "processing_error" not in st.session_state:
    st.session_state.processing_error = None

# ─── Sidebar ───────────────────────────────────────────────────────────────────
render_sidebar()

# ─── Header ────────────────────────────────────────────────────────────────────
render_header()

# ─── Upload section ────────────────────────────────────────────────────────────
uploaded_file = render_upload_section()
if uploaded_file is not None:
    st.session_state.uploaded_file = uploaded_file

    file_bytes = uploaded_file.getvalue()
    file_hash = hashlib.md5(file_bytes).hexdigest()
    uploaded_signature = f"{uploaded_file.name}:{uploaded_file.size}:{file_hash}"

    if uploaded_signature != st.session_state.uploaded_signature:
        try:
            data_dir = Path("data")
            pdf_dir = data_dir / "pdfs"
            index_dir = data_dir / "faiss_index" / file_hash
            pdf_dir.mkdir(parents=True, exist_ok=True)
            index_dir.parent.mkdir(parents=True, exist_ok=True)

            safe_name = Path(uploaded_file.name).name
            pdf_path = pdf_dir / safe_name
            with open(pdf_path, "wb") as f:
                f.write(file_bytes)

            st.session_state.processing_step = 1
            st.session_state.answer = None
            st.session_state.processing_error = None

            with st.spinner("Đang xử lý tài liệu PDF và tạo chỉ mục..."):
                st.session_state.processing_step = 2
                vector_db,chunks = process_pdf_to_vectorstore(
                    pdf_path=str(pdf_path),
                    vector_store_path=str(index_dir),
                )

            st.session_state.vector_db = vector_db
            st.session_state.chunks = chunks
            st.session_state.processing_step = 3
            st.session_state.uploaded_signature = uploaded_signature
            st.success("Tài liệu đã sẵn sàng để hỏi đáp.")
        except Exception as exc:
            st.session_state.processing_error = str(exc)
            st.session_state.vector_db = None
            st.session_state.processing_step = 1
            st.error(f"Không thể xử lý PDF: {exc}")

# ─── Processing pipeline ───────────────────────────────────────────────────────
progress_map = {1: 30, 2: 65, 3: 100}
render_pipeline(progress=progress_map.get(st.session_state.processing_step, 0))

# ─── Q&A section ───────────────────────────────────────────────────────────────
question, send_clicked = render_qa_section()

if send_clicked:
    if not question:
        st.warning("Vui lòng nhập câu hỏi trước khi gửi.")
    elif st.session_state.vector_db is None:
        st.warning("Vui lòng upload và xử lý PDF trước khi đặt câu hỏi.")
    else:
        try:
            with st.spinner("SmartDoc AI đang phân tích câu hỏi..."):
                response_text, sources, hybrid_response_text, hybrid_sources = get_answer(question, st.session_state.vector_db,st.session_state.chunks)

            source_text = "Nguồn: " + (", ".join(sources) if sources else "Không xác định")
            st.session_state.answer = {
                "text": response_text,
                "source": source_text,
            }
            hybrid_source_text = "Nguồn: " + (", ".join(hybrid_sources) if hybrid_sources else "Không xác định")
            st.session_state.hybrid_answer = {
                "text": hybrid_response_text,
                "source": hybrid_source_text,
            }
        except Exception as exc:
            st.error(f"Lỗi khi chạy RAG chain: {exc}")

if st.session_state.answer and st.session_state.hybrid_answer:
    render_answer(
        st.session_state.answer,
        st.session_state.hybrid_answer
    )

# ─── Status FAB ────────────────────────────────────────────────────────────────
render_status_fab()
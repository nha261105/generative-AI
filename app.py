import streamlit as st
import hashlib
from pathlib import Path

from data.history import new_conversation, add_message, load_conversations, delete_conversation
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
if "processing_step" not in st.session_state:
    st.session_state.processing_step = 1  # 1=reading, 2=embedding, 3=ready
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None
if "uploaded_signature" not in st.session_state:
    st.session_state.uploaded_signature = None
if "processing_error" not in st.session_state:
    st.session_state.processing_error = None
if "active_conversation_id" not in st.session_state:
    st.session_state.active_conversation_id = None

# ─── Sidebar ───────────────────────────────────────────────────────────────────
chat_history = load_conversations()
history_by_id = {conv.get("id"): conv for conv in chat_history}
selected_conv_id, deleted_conv_id = render_sidebar(
    chat_history=chat_history,
    active_conversation_id=st.session_state.active_conversation_id,
)

if deleted_conv_id:
    deleted_ok = delete_conversation(deleted_conv_id)
    if deleted_ok:
        if st.session_state.active_conversation_id == deleted_conv_id:
            st.session_state.active_conversation_id = None
            st.session_state.answer = None
            st.session_state.question_input = ""
        st.rerun()
    else:
        st.warning("Không tìm thấy cuộc trò chuyện để xóa.")

if selected_conv_id:
    st.session_state.active_conversation_id = selected_conv_id
    selected_conv = history_by_id.get(selected_conv_id)

    if selected_conv and selected_conv.get("messages"):
        last_message = selected_conv["messages"][-1]
        st.session_state.answer = {
            "text": last_message.get("answer", ""),
            "source": last_message.get("source", "Nguồn: Không xác định"),
        }
        st.session_state.question_input = last_message.get("question", "")
    else:
        st.session_state.answer = None
        st.session_state.question_input = ""

    st.rerun()

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
                vector_db = process_pdf_to_vectorstore(
                    pdf_path=str(pdf_path),
                    vector_store_path=str(index_dir),
                )

            st.session_state.vector_db = vector_db
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
                response_text, sources = get_answer(question, st.session_state.vector_db)

            source_text = "Nguồn: " + (", ".join(sources) if sources else "Không xác định")

            active_conv_id = st.session_state.active_conversation_id
            if not active_conv_id:
                current_doc_name = (
                    st.session_state.uploaded_file.name
                    if st.session_state.uploaded_file is not None
                    else ""
                )
                created_conv = new_conversation(doc_name=current_doc_name)
                active_conv_id = created_conv["id"]
                st.session_state.active_conversation_id = active_conv_id

            saved_conv = add_message(
                conv_id=active_conv_id,
                question=question,
                answer=response_text,
                source=source_text,
            )

            if saved_conv is None:
                current_doc_name = (
                    st.session_state.uploaded_file.name
                    if st.session_state.uploaded_file is not None
                    else ""
                )
                created_conv = new_conversation(doc_name=current_doc_name)
                st.session_state.active_conversation_id = created_conv["id"]
                add_message(
                    conv_id=created_conv["id"],
                    question=question,
                    answer=response_text,
                    source=source_text,
                )

            st.session_state.answer = {
                "text": response_text,
                "source": source_text,
            }
        except Exception as exc:
            st.error(f"Lỗi khi chạy RAG chain: {exc}")

if st.session_state.answer:
    render_answer(st.session_state.answer)

# ─── Status FAB ────────────────────────────────────────────────────────────────
render_status_fab()
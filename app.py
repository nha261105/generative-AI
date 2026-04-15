import streamlit as st
import hashlib
from pathlib import Path

from data.history import (
    new_conversation,
    add_message,
    load_conversations,
    delete_conversation,
    get_conversation,
    clear_all,
    clear_vector_store_directory,
)
from src.presentation.styles import get_css
from src.presentation.components import (
    render_sidebar,
    render_collapsed_sidebar_toggle,
    render_header,
    render_upload_section,
    render_processing_timeline,
    render_qa_section,
    render_conversation_history,
)

from src.application.pipeline import process_pdf_to_vectorstore
from src.application.chain_citation import get_answer_with_citation
from src.application.chain_hybrid import get_answer_with_hybrid_citation
from src.presentation.comp_citation import render_answer

# ─── Page config (phải đặt đầu tiên) ──────────────────────────────────────────
st.set_page_config(
    page_title="SmartDoc AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Inject CSS từ styles.py ───────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "sidebar_collapsed" not in st.session_state:
    st.session_state.sidebar_collapsed = False
if "selected_message_index" not in st.session_state:
    st.session_state.selected_message_index = None

st.markdown(
    get_css(
        dark_mode=st.session_state.dark_mode,
        sidebar_collapsed=st.session_state.sidebar_collapsed,
    ),
    unsafe_allow_html=True,
)

# ─── Session state ─────────────────────────────────────────────────────────────
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "answer" not in st.session_state:
    st.session_state.answer = None
if "processing_step" not in st.session_state:
    st.session_state.processing_step = 0  # 0=pending, 1=reading, 2=embedding, 3=ready
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None
if "uploaded_signature" not in st.session_state:
    st.session_state.uploaded_signature = None
if "processing_error" not in st.session_state:
    st.session_state.processing_error = None
if "active_conversation_id" not in st.session_state:
    st.session_state.active_conversation_id = None
if "chunk_size" not in st.session_state:
    st.session_state.chunk_size = 1000
if "chunk_overlap" not in st.session_state:
    st.session_state.chunk_overlap = 150
if "retrieval_mode" not in st.session_state:
    st.session_state.retrieval_mode = "vector"

MAX_UPLOAD_MB = 25

# ─── Sidebar ───────────────────────────────────────────────────────────────────
chat_history = load_conversations()
history_by_id = {conv.get("id"): conv for conv in chat_history}
if st.session_state.sidebar_collapsed:
    selected_conv_id = None
    deleted_conv_id = None
    new_chat_clicked = False
    toggle_sidebar_clicked = render_collapsed_sidebar_toggle()
else:
    (
        selected_conv_id,
        deleted_conv_id,
        new_chat_clicked,
        toggle_sidebar_clicked,
        clear_history_clicked,
        clear_vector_clicked,
        selected_chunk_size,
        selected_chunk_overlap,
        selected_retrieval_mode,
    ) = render_sidebar(
        chat_history=chat_history,
        active_conversation_id=st.session_state.active_conversation_id,
        dark_mode=st.session_state.dark_mode,
        chunk_size=st.session_state.chunk_size,
        chunk_overlap=st.session_state.chunk_overlap,
        retrieval_mode=st.session_state.retrieval_mode,
    )

if st.session_state.sidebar_collapsed:
    clear_history_clicked = False
    clear_vector_clicked = False
    selected_chunk_size = st.session_state.chunk_size
    selected_chunk_overlap = st.session_state.chunk_overlap
    selected_retrieval_mode = st.session_state.retrieval_mode

st.session_state.chunk_size = selected_chunk_size
st.session_state.chunk_overlap = selected_chunk_overlap
st.session_state.retrieval_mode = selected_retrieval_mode

if toggle_sidebar_clicked:
    st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
    st.rerun()

if clear_history_clicked:
    clear_all()
    st.session_state.active_conversation_id = None
    st.session_state.answer = None
    st.session_state.question_input = ""
    st.session_state.selected_message_index = None
    st.success("Đã xóa toàn bộ lịch sử hội thoại.")
    st.rerun()

if clear_vector_clicked:
    if clear_vector_store_directory():
        st.session_state.vector_db = None
        st.session_state.uploaded_signature = None
        st.session_state.uploaded_file = None
        st.session_state.processing_step = 0
        st.session_state.processing_error = None
        st.success("Đã xóa vector store và tài liệu đã tải lên.")
        st.rerun()
    st.error("Không thể xóa vector store. Vui lòng thử lại.")

if new_chat_clicked:
    st.session_state.active_conversation_id = None
    st.session_state.answer = None
    st.session_state.question_input = ""
    st.session_state.uploaded_file = None
    st.session_state.vector_db = None
    st.session_state.uploaded_signature = None
    st.session_state.processing_error = None
    st.session_state.processing_step = 0
    st.session_state.selected_message_index = None
    st.rerun()

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
        st.session_state.selected_message_index = len(selected_conv["messages"]) - 1
    else:
        st.session_state.answer = None
        st.session_state.question_input = ""
        st.session_state.selected_message_index = None

    st.rerun()

# ─── Header ────────────────────────────────────────────────────────────────────
selected_dark_mode = render_header(dark_mode=st.session_state.dark_mode)

if selected_dark_mode != st.session_state.dark_mode:
    st.session_state.dark_mode = selected_dark_mode
    st.rerun()

# ─── Upload section ────────────────────────────────────────────────────────────
uploaded_file = render_upload_section()
if uploaded_file is not None:
    st.session_state.uploaded_file = uploaded_file

    if uploaded_file.size > MAX_UPLOAD_MB * 1024 * 1024:
        st.session_state.processing_error = "File PDF vuot qua gioi han 25 MB."
        st.session_state.vector_db = None
        st.session_state.processing_step = 0
        st.error("File PDF vuot qua gioi han 25 MB.")
    elif not uploaded_file.name.lower().endswith(".pdf"):
        st.session_state.processing_error = "Chi chap nhan file PDF."
        st.session_state.vector_db = None
        st.session_state.processing_step = 0
        st.error("Chi chap nhan file PDF.")
    else:
        file_bytes = uploaded_file.getvalue()
        file_hash = hashlib.md5(file_bytes).hexdigest()
        uploaded_signature = (
            f"{uploaded_file.name}:{uploaded_file.size}:{file_hash}:"
            f"{st.session_state.chunk_size}:{st.session_state.chunk_overlap}"
        )

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
                        chunk_size=st.session_state.chunk_size,
                        chunk_overlap=st.session_state.chunk_overlap,
                    )

                st.session_state.vector_db = vector_db
                st.session_state.processing_step = 3
                st.session_state.uploaded_signature = uploaded_signature
                st.success("Upload file thành công. Bạn có thể bắt đầu hỏi đáp.")
            except Exception as exc:
                st.session_state.processing_error = str(exc)
                st.session_state.vector_db = None
                st.session_state.processing_step = 0
                st.error(f"Không thể xử lý PDF: {exc}")

render_processing_timeline(st.session_state.processing_step)

# ─── Q&A section ───────────────────────────────────────────────────────────────
question, send_clicked = render_qa_section()

if send_clicked:
    if not question:
        st.warning("Vui lòng nhập câu hỏi trước khi gửi.")
    elif st.session_state.vector_db is None:
        st.warning("Vui lòng upload và xử lý PDF trước khi đặt câu hỏi.")
    else:
        try:
            active_conversation = get_conversation(st.session_state.active_conversation_id)
            chat_context = active_conversation.get("messages", []) if active_conversation else []

            with st.spinner("SmartDoc AI đang phân tích câu hỏi..."):
                if st.session_state.retrieval_mode == "hybrid":
                    response, sources = get_answer_with_hybrid_citation(
                        question,
                        st.session_state.vector_db,
                        chat_history=chat_context,
                    )
                else:
                    response, sources = get_answer_with_citation(
                        question,
                        st.session_state.vector_db,
                        chat_history=chat_context,
                    )

            source_pages = sorted({src.get("page") for src in sources if src.get("page") is not None})
            source_text = (
                "Nguồn: " + ", ".join([f"Trang {page}" for page in source_pages])
                if source_pages
                else "Nguồn: Không xác định"
            )

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
                answer=response,
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
                    answer=response,
                    source=source_text,
                )
            st.session_state.answer = {
                "text": response,
                "sources": sources,
                "query": question
            }

            active_conversation = get_conversation(st.session_state.active_conversation_id)
            if active_conversation and active_conversation.get("messages"):
                st.session_state.selected_message_index = len(active_conversation["messages"]) - 1
        except Exception as exc:
            st.error(f"Lỗi khi chạy RAG chain: {exc}")

if st.session_state.answer:
    render_answer(st.session_state.answer)

if st.session_state.active_conversation_id:
    conv = get_conversation(st.session_state.active_conversation_id)
    messages = conv.get("messages", []) if conv else []
    st.session_state.selected_message_index = render_conversation_history(
        messages=messages,
        selected_index=st.session_state.selected_message_index,
        key_prefix=st.session_state.active_conversation_id,
    )

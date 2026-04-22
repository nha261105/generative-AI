import streamlit as st
import hashlib
from pathlib import Path
from data.history import (
    add_message,
    clear_all,
    clear_vector_store_directory,
    delete_conversation,
    get_conversation,
    load_conversations,
    new_conversation,
)
from src.application.chain_citation import get_answer_with_citation
from src.application.chain_hybrid import get_answer_with_hybrid_citation
from src.application.chain_multidoc import get_answer_multidoc
from src.application.pipeline import process_pdf_to_vectorstore
from src.application.pipeline_docx import process_docx_to_vectorstore
from src.presentation.comp_citation import render_answer as render_citation_answer
from src.presentation.comp_multidoc import render_doc_filter
from src.presentation.components import (
    render_answer,
    render_collapsed_sidebar_toggle,
    render_conversation_history,
    render_header,
    render_processing_timeline,
    render_qa_section,
    render_sidebar,
    render_upload_section,
)
from src.presentation.styles import get_css


st.set_page_config(
    page_title="SmartDoc AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


def normalize_sources(raw_sources) -> list[dict]:
    """Chuẩn hóa sources để UI citation không bị vỡ schema."""
    normalized = []
    for i, src in enumerate(raw_sources or [], start=1):
        if isinstance(src, dict):
            normalized.append(
                {
                    "id": src.get("id", i),
                    "page": src.get("page", "?"),
                    "content": str(src.get("content", "")).strip(),
                    "source_file": src.get("source_file", "Tài liệu"),
                }
            )
            continue

        source_text = str(src).strip()
        source_file = "Tài liệu"
        page = "?"
        if " - Trang " in source_text:
            source_file, _, raw_page = source_text.partition(" - Trang ")
            source_file = source_file.strip() or "Tài liệu"
            page = raw_page.strip() or "?"

        normalized.append(
            {
                "id": i,
                "page": page,
                "content": source_text,
                "source_file": source_file,
            }
        )

    return normalized


def build_source_text(sources: list[dict]) -> str:
    labels = []
    for src in sources:
        source_file = str(src.get("source_file", "Tài liệu")).strip() or "Tài liệu"
        page = src.get("page")
        if page in (None, "", "?"):
            labels.append(source_file)
        else:
            labels.append(f"{source_file} - Trang {page}")

    unique_labels = list(dict.fromkeys(labels))
    return "Nguồn: " + (", ".join(unique_labels) if unique_labels else "Không xác định")


# Theme + local UI states
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


# Core states
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "answer" not in st.session_state:
    st.session_state.answer = None
if "processing_step" not in st.session_state:
    st.session_state.processing_step = 0
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
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if "use_multidoc" not in st.session_state:
    st.session_state.use_multidoc = False

MAX_UPLOAD_MB = 25


# Sidebar
chat_history = load_conversations()
history_by_id = {conv.get("id"): conv for conv in chat_history}

if st.session_state.sidebar_collapsed:
    selected_conv_id = None
    deleted_conv_id = None
    new_chat_clicked = False
    clear_history_clicked = False
    clear_vector_clicked = False
    selected_chunk_size = st.session_state.chunk_size
    selected_chunk_overlap = st.session_state.chunk_overlap
    selected_retrieval_mode = st.session_state.retrieval_mode
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

if deleted_conv_id:
    deleted_ok = delete_conversation(deleted_conv_id)
    if deleted_ok:
        if st.session_state.active_conversation_id == deleted_conv_id:
            st.session_state.active_conversation_id = None
            st.session_state.answer = None
            st.session_state.question_input = ""
            st.session_state.selected_message_index = None
        st.rerun()
    st.warning("Không tìm thấy cuộc trò chuyện để xóa.")

if new_chat_clicked:
    st.session_state.active_conversation_id = None
    st.session_state.answer = None
    st.session_state.question_input = ""
    st.session_state.selected_message_index = None
    st.session_state.last_question = ""
    st.rerun()

if selected_conv_id:
    st.session_state.active_conversation_id = selected_conv_id
    selected_conv = history_by_id.get(selected_conv_id)
    if selected_conv and selected_conv.get("messages"):
        last_message = selected_conv["messages"][-1]
        st.session_state.answer = {
            "text": last_message.get("answer", ""),
            "source": last_message.get("source", "Nguồn: Không xác định"),
            "sources": normalize_sources(last_message.get("sources", [])),
            "query": last_message.get("question", ""),
        }
        st.session_state.question_input = last_message.get("question", "")
        st.session_state.selected_message_index = len(selected_conv["messages"]) - 1
    else:
        st.session_state.answer = None
        st.session_state.question_input = ""
        st.session_state.selected_message_index = None
    st.rerun()


# Header
selected_dark_mode = render_header(dark_mode=st.session_state.dark_mode)
if selected_dark_mode != st.session_state.dark_mode:
    st.session_state.dark_mode = selected_dark_mode
    st.rerun()


# Upload
uploaded_file = render_upload_section()
if uploaded_file is not None:
    st.session_state.uploaded_file = uploaded_file

    if uploaded_file.size > MAX_UPLOAD_MB * 1024 * 1024:
        st.session_state.processing_error = "File vượt quá giới hạn 25 MB."
        st.session_state.vector_db = None
        st.session_state.processing_step = 0
        st.error(st.session_state.processing_error)
    elif not uploaded_file.name.lower().endswith((".pdf", ".docx")):
        st.session_state.processing_error = "Chỉ chấp nhận file PDF hoặc DOCX."
        st.session_state.vector_db = None
        st.session_state.processing_step = 0
        st.error(st.session_state.processing_error)
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

                with st.spinner("Đang xử lý tài liệu và tạo chỉ mục..."):
                    st.session_state.processing_step = 2
                    file_path = str(pdf_path)
                    file_ext = uploaded_file.name.lower()
                    if file_ext.endswith(".pdf"):
                        vector_db = process_pdf_to_vectorstore(
                            pdf_path=file_path,
                            vector_store_path=str(index_dir),
                            chunk_size=st.session_state.chunk_size,
                            chunk_overlap=st.session_state.chunk_overlap,
                        )
                    elif file_ext.endswith(".docx"):
                        vector_db = process_docx_to_vectorstore(
                            docx_path=file_path,
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
                st.error(f"Không thể xử lý file: {exc}")


# Processing timeline
render_processing_timeline(st.session_state.processing_step)


# Feature toggles
st.markdown("#### Tùy chọn truy vấn")
st.session_state.use_multidoc = st.toggle(
    "Bật lọc tài liệu (Multidoc)",
    value=st.session_state.use_multidoc,
)

metadata_filter = None
if st.session_state.use_multidoc:
    metadata_filter = render_doc_filter(st.session_state.vector_db)
    if st.session_state.retrieval_mode == "hybrid":
        st.caption("Multidoc đang bật: hệ thống sẽ ưu tiên truy xuất theo bộ lọc tài liệu.")


# Question input
question, send_clicked = render_qa_section()


# RAG flow
if send_clicked:
    if not question:
        st.warning("Vui lòng nhập câu hỏi trước khi gửi.")
    elif st.session_state.vector_db is None:
        st.warning("Vui lòng upload PDF trước khi đặt câu hỏi.")
    elif question == st.session_state.last_question:
        st.info("Câu hỏi này vừa được xử lý, vui lòng đổi câu hỏi hoặc hỏi tiếp.")
    else:
        try:
            active_conversation = get_conversation(st.session_state.active_conversation_id)
            chat_context = active_conversation.get("messages", []) if active_conversation else []

            with st.spinner("SmartDoc AI đang phân tích câu hỏi..."):
                comparison = None

                if st.session_state.use_multidoc:
                    response, raw_sources = get_answer_multidoc(
                        question,
                        st.session_state.vector_db,
                        metadata_filter=metadata_filter,
                    )
                elif st.session_state.retrieval_mode == "hybrid":
                    vector_response, vector_raw_sources = get_answer_with_citation(
                        question,
                        st.session_state.vector_db,
                        chat_history=chat_context,
                    )
                    hybrid_response, hybrid_raw_sources = get_answer_with_hybrid_citation(
                        question,
                        st.session_state.vector_db,
                        chat_history=chat_context,
                    )

                    vector_sources = normalize_sources(vector_raw_sources)
                    hybrid_sources = normalize_sources(hybrid_raw_sources)

                    comparison = {
                        "vector": {
                            "text": vector_response,
                            "source": build_source_text(vector_sources),
                        },
                        "hybrid": {
                            "text": hybrid_response,
                            "source": build_source_text(hybrid_sources),
                        },
                    }

                    response = hybrid_response
                    raw_sources = hybrid_raw_sources
                else:
                    response, raw_sources = get_answer_with_citation(
                        question,
                        st.session_state.vector_db,
                        chat_history=chat_context,
                    )

            sources = normalize_sources(raw_sources)
            source_text = build_source_text(sources)

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
                "source": source_text,
                "sources": sources,
                "query": question,
                "retrieval_mode": st.session_state.retrieval_mode,
                "comparison": comparison,
            }
            st.session_state.last_question = question

            active_conversation = get_conversation(st.session_state.active_conversation_id)
            if active_conversation and active_conversation.get("messages"):
                st.session_state.selected_message_index = len(active_conversation["messages"]) - 1
        except Exception as exc:
            st.error(f"Lỗi khi chạy RAG chain: {exc}")


# Render answer
if st.session_state.answer:
    answer_payload = st.session_state.answer
    comparison = answer_payload.get("comparison")

    if answer_payload.get("retrieval_mode") == "hybrid" and comparison:
        render_answer(comparison["vector"], comparison["hybrid"])
        st.markdown("#### Kết quả Hybrid (chi tiết nguồn)")

    render_citation_answer(answer_payload)


# Conversation history panel
if st.session_state.active_conversation_id:
    conv = get_conversation(st.session_state.active_conversation_id)
    messages = conv.get("messages", []) if conv else []
    st.session_state.selected_message_index = render_conversation_history(
        messages=messages,
        selected_index=st.session_state.selected_message_index,
        key_prefix=st.session_state.active_conversation_id,
    )

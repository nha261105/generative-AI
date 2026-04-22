import streamlit as st
from langchain_core.documents import Document


def _get_documents_from_vector_store(vector_db) -> list[Document]:
    """Extract all documents from FAISS docstore."""
    docstore = getattr(vector_db, "docstore", None)
    if docstore is None:
        return []
    raw_dict = getattr(docstore, "_dict", {})
    return [doc for doc in raw_dict.values() if isinstance(doc, Document)]


def _build_file_list(vector_db) -> dict[str, str]:
    """Build {display_name: filename} mapping from vector store metadata."""
    docs = _get_documents_from_vector_store(vector_db)
    file_map = {}

    for doc in docs:
        meta = doc.metadata or {}
        filename = meta.get("filename", "")
        if not filename:
            # Fallback to source field
            source = meta.get("source", "")
            if source:
                filename = source.split("/")[-1]
        if not filename:
            continue

        upload_time = meta.get("upload_time", "")
        file_type = meta.get("file_type", "")

        date_part = upload_time.split(" ")[0] if upload_time else "N/A"
        display = f"{filename} ({date_part}, {file_type})" if file_type else filename
        file_map[display] = filename

    return file_map


def render_doc_filter(vector_db):
    """Render document filter multiselect. Returns metadata filter dict or None."""
    if vector_db is None:
        st.caption("Chưa có vector store. Upload PDF trước.")
        return None

    file_map = _build_file_list(vector_db)

    if not file_map:
        st.caption("Không tìm thấy metadata tài liệu.")
        return None

    file_list = sorted(file_map.keys())

    selected = st.multiselect(
        "📂 Lọc theo tài liệu",
        options=file_list,
        default=[],
        placeholder="Tất cả tài liệu",
    )

    if not selected:
        return None

    # Single file → exact match filter for FAISS
    if len(selected) == 1:
        return {"filename": file_map[selected[0]]}

    # Multiple files → return list of filenames (handled in chain_multidoc)
    return {"filename": [file_map[s] for s in selected]}
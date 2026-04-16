import streamlit as st


# CACHE FILTER (FIX CHẬM)
@st.cache_data
def build_filter_cache(_vector_db):
    docs = _vector_db.docstore._dict.values()

    file_map = {}

    for doc in docs:
        filename = doc.metadata.get("filename")
        upload_time = doc.metadata.get("upload_time", "unknown")
        file_type = doc.metadata.get("file_type", "unknown")

        if filename:
            date_only = upload_time.split(" ")[0] if upload_time != "unknown" else "unknown"

            display_name = f"{filename} - {date_only} - {file_type}"
            file_map[display_name] = filename

    return file_map


# UI FILTER
def render_doc_filter(vector_db):
    if vector_db is None:
        return None

    file_map = build_filter_cache(vector_db)

    file_list = sorted(file_map.keys())

    selected = st.selectbox(
        "📂 Chọn tài liệu (tên - ngày - loại)",
        ["Tất cả"] + file_list
    )

    if selected == "Tất cả":
        return None

    return {"filename": file_map[selected]}
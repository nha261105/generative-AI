# import streamlit as st


# def render_doc_filter(vector_db):
#     if vector_db is None:
#         return None

#     docs = vector_db.docstore._dict.values()

#     # docs = [
#     # Document(..., metadata={"filename": "file1.pdf"}),
#     # Document(..., metadata={"filename": "file1.pdf"}),
#     # Document(..., metadata={"filename": "file2.pdf"})
#     # ]

#     file_set = set()
#     # set->loại trùng filename

#     file_map = {}  # key: display string -> filename

#     for doc in docs:
#         filename = doc.metadata.get("filename")
#         upload_time = doc.metadata.get("upload_time", "unknown")
#         file_type = doc.metadata.get("file_type", "unknown")

#         if filename:
#             date_only = upload_time.split(" ")[0] if upload_time != "unknown" else "unknown"

#             display_name = f"{filename} - {date_only} - {file_type}"

#             file_set.add(filename)
#             file_map[display_name] = filename

#     # file_set = {"file1.pdf", "file2.pdf"}

#     file_list = sorted(list(file_map.keys()))
    
#     # đúng thứ tự
#     # ["file1.pdf", "file2.pdf"]

#     selected = st.selectbox(
#         "📂 Chọn tài liệu",
#         ["Tất cả"] + file_list
#     )

#     if selected == "Tất cả":
#         return None
#     else:
#         # trả về đúng filename
#         return {"filename": file_map[selected]}


import streamlit as st


# =========================
# CACHE FILTER (FIX CHẬM)
# =========================
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


# =========================
# UI FILTER
# =========================
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
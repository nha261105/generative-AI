import streamlit as st
from langchain_community.llms import Ollama
from langchain_core.documents import Document
from src.application.prompts import get_rag_prompt


@st.cache_resource
def _get_llm():
    return Ollama(
        model="qwen2.5:7b",
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
    )


def _filter_docs_manually(docs: list[Document], filenames: list[str]) -> list[Document]:
    """Filter documents by a list of filenames (for multi-select filter)."""
    return [
        doc for doc in docs
        if (doc.metadata.get("filename") or doc.metadata.get("source", "").split("/")[-1])
        in filenames
    ]


def get_answer_multidoc(query: str, vector_db, metadata_filter=None):
    llm = _get_llm()

    search_kwargs = {"k": 4, "fetch_k": 12}

    # Determine filter approach
    multi_filenames = None
    if metadata_filter:
        filenames_value = metadata_filter.get("filename")
        if isinstance(filenames_value, list):
            # Multi-file filter — FAISS doesn't support OR filter natively,
            # so we retrieve more docs and filter manually
            multi_filenames = filenames_value
            search_kwargs["k"] = 8
        elif filenames_value:
            # Single file → FAISS exact match filter
            search_kwargs["filter"] = {"filename": filenames_value}

    retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs,
    )

    docs = retriever.invoke(query)

    # Manual multi-file filter
    if multi_filenames:
        docs = _filter_docs_manually(docs, multi_filenames)

    if not docs:
        return (
            "Mình chưa tìm thấy ngữ cảnh phù hợp với bộ lọc tài liệu hiện tại. "
            "Bạn hãy thử chọn 'Tất cả' hoặc đặt lại câu hỏi cụ thể hơn.",
            [
                {
                    "id": 1,
                    "page": "?",
                    "content": "Không tìm thấy đoạn trích phù hợp cho bộ lọc hiện tại.",
                    "source_file": "Không xác định",
                }
            ],
        )

    # Build context
    context = "\n\n".join([doc.page_content for doc in docs])

    # Sources — consistent schema for citation rendering
    sources = []
    for i, doc in enumerate(docs, start=1):
        metadata = doc.metadata or {}
        raw_page = metadata.get("page", 0)
        page = raw_page + 1 if isinstance(raw_page, int) else (raw_page or "?")
        source_file = str(
            metadata.get("filename")
            or metadata.get("source")
            or "Tài liệu"
        ).split("/")[-1]

        sources.append(
            {
                "id": i,
                "page": page,
                "content": doc.page_content,
                "source_file": source_file,
            }
        )

    prompt = get_rag_prompt().format(
        context=context,
        question=query,
    )

    response = llm.invoke(prompt)

    return response, sources
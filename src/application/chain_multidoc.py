import streamlit as st
from langchain_community.llms import Ollama
from src.application.promts import get_rag_prompt


# CACHE LLM (FIX QUAN TRỌNG)
@st.cache_resource
def get_llm():
    return Ollama(
        model="qwen2.5:7b",
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
    )


def get_answer_multidoc(query: str, vector_db, metadata_filter=None):
    llm = get_llm()

    search_kwargs = {"k": 2, "fetch_k": 5}

    # GẮN FILTER
    if metadata_filter:
        search_kwargs["filter"] = metadata_filter

    retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs
    )

    # RETRIEVE
    docs = retriever.invoke(query)

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

    # BUILD CONTEXT
    context = "\n\n".join([doc.page_content for doc in docs])

    # SOURCE chi tiết để render citation nhất quán
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
        question=query
    )

    response = llm.invoke(prompt)

    return response, sources
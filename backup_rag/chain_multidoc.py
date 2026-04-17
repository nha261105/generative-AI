# import streamlit as st
# from langchain_community.llms import Ollama
# from src.application.promts import get_rag_prompt

# @st.cache_resource
# def get_llm():
#     return Ollama(
#         model="qwen2.5:7b",
#         temperature=0.7,
#         top_p=0.9,
#         repeat_penalty=1.1,
#     )

# def get_answer_multidoc(query: str, vector_db, metadata_filter=None):
#     llm = get_llm()

#     search_kwargs = {"k": 3,"fetch_k": 10}

#     # GẮN FILTER
#     if metadata_filter:
#         search_kwargs["filter"] = metadata_filter
        
#     # nếu có lọc
#     # search_kwargs = {
#     # "k": 3,
#     # "fetch_k": 10,
#     # "filter": {"filename": "file1.pdf"}
#     # }

#     retriever = vector_db.as_retriever(
#         search_type="mmr",
#         search_kwargs=search_kwargs
#     )

#     # RETRIEVE
#     docs = retriever.invoke(query)

#     # BUILD CONTEXT
#     context = "\n\n".join([doc.page_content for doc in docs])

#     # SOURCE
#     sources = list(set([
#         f"{doc.metadata.get('filename', 'Unknown')} - Trang {doc.metadata.get('page', 0)+1}"
#         for doc in docs
#     ]))

#     prompt = get_rag_prompt().format(
#         context=context,
#         question=query
#     )

#     response = llm.invoke(prompt)

#     return response, sources



import streamlit as st
from langchain_community.llms import Ollama
from src.application.promts import get_rag_prompt


# =========================
# CACHE LLM (FIX QUAN TRỌNG)
# =========================
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

    # BUILD CONTEXT
    context = "\n\n".join([doc.page_content for doc in docs])

    # SOURCE
    sources = list(set([
        f"{doc.metadata.get('filename', 'Unknown')} - Trang {doc.metadata.get('page', 0)+1}"
        for doc in docs
    ]))

    prompt = get_rag_prompt().format(
        context=context,
        question=query
    )

    response = llm.invoke(prompt)

    return response, sources
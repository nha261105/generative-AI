from langchain.retrievers import EnsembleRetriever
from langchain_community.llms import Ollama

from src.data_layer.vector_store import (
    get_vector_retriever,
    get_bm25_retriever,
    create_hybrid_retriever_from_vector_store,
)
from src.application.promts import get_rag_prompt, get_rag_prompt_with_history

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from typing import List, Dict, Tuple


def create_hybrid_retriever(

        vector_store: FAISS,
        chunks: List[Document],
        k: int = 3

):

    # Vector retriever
    vector_retriever = get_vector_retriever(
        vector_store,
        k
    )

    # BM25 retriever
    bm25_retriever = get_bm25_retriever(
        chunks,
        k
    )   

    # Hybrid (Ensemble)
    hybrid_retriever = EnsembleRetriever(

        retrievers=[
            vector_retriever,
            bm25_retriever
        ],

        weights=[0.7,0.3]

    )

    return hybrid_retriever


def _format_chat_history(chat_history: List[Dict] | None, max_turns: int = 5) -> str:
    if not chat_history:
        return "(Chưa có lịch sử hội thoại)"

    recent_turns = chat_history[-max_turns:]
    lines: List[str] = []
    for turn in recent_turns:
        question = (turn.get("question") or "").strip()
        answer = (turn.get("answer") or "").strip()

        if question:
            lines.append(f"Người dùng: {question}")
        if answer:
            lines.append(f"Trợ lý: {answer}")

    return "\n".join(lines) if lines else "(Chưa có lịch sử hội thoại)"


def get_answer_with_hybrid_citation(
    query: str,
    vector_store: FAISS,
    chat_history: List[Dict] | None = None,
    k: int = 3,
) -> Tuple[str, List[Dict]]:
    llm = Ollama(
        model="qwen2.5:7b",
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
    )

    retriever = create_hybrid_retriever_from_vector_store(vector_store=vector_store, k=k)
    relevant_docs = retriever.invoke(query)

    context_list: List[str] = []
    detailed_sources: List[Dict] = []

    for i, doc in enumerate(relevant_docs):
        source_id = i + 1
        page_num = doc.metadata.get("page", 0) + 1
        content = doc.page_content

        context_list.append(f"[Nguồn {source_id} | Trang {page_num}]: {content}")
        detailed_sources.append(
            {
                "id": source_id,
                "page": page_num,
                "content": content,
                "source_file": doc.metadata.get("source", "N/A"),
            }
        )

    context_string = "\n\n".join(context_list)

    if chat_history:
        prompt = get_rag_prompt_with_history().format(
            chat_history=_format_chat_history(chat_history),
            context=context_string,
            question=query,
        )
    else:
        prompt = get_rag_prompt().format(
            context=context_string,
            question=query,
        )

    response = llm.invoke(prompt)
    return response, detailed_sources
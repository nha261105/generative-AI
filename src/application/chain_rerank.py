from typing import Dict, List, Tuple
from functools import lru_cache
import time

from langchain_community.llms import Ollama
from sentence_transformers import CrossEncoder

from src.application.prompts import get_rag_prompt, get_rag_prompt_with_history


@lru_cache(maxsize=1)
def _get_reranker() -> CrossEncoder:
    # Cache model để tránh tải lại mỗi câu hỏi, giúp giảm latency rõ rệt.
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


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


def get_answer_with_rerank_citation(
    query: str,
    vector_db,
    chat_history: List[Dict] | None = None,
    fetch_k: int = 12,
    top_k: int = 3,
) -> Tuple[str, List[Dict], Dict]:
    start_ts = time.perf_counter()
    llm = Ollama(
        model="qwen2.5:7b",
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
    )

    retriever = vector_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": fetch_k, "fetch_k": max(fetch_k, 20)},
    )
    retrieve_start = time.perf_counter()
    candidate_docs = retriever.invoke(query)
    retrieve_time = time.perf_counter() - retrieve_start

    if not candidate_docs:
        return (
            "Mình chưa tìm thấy ngữ cảnh phù hợp trong tài liệu đã index để trả lời an toàn. "
            "Bạn hãy thử diễn đạt lại câu hỏi hoặc upload thêm tài liệu liên quan.",
            [
                {
                    "id": 1,
                    "page": "?",
                    "content": "Không tìm thấy đoạn trích phù hợp trong tài liệu hiện tại.",
                    "source_file": "Không xác định",
                }
            ],
            {
                "retrieve_time_sec": round(retrieve_time, 3),
                "rerank_time_sec": 0.0,
                "llm_time_sec": 0.0,
                "total_time_sec": round(time.perf_counter() - start_ts, 3),
                "candidate_count": 0,
                "returned_count": 0,
            },
        )

    rerank_start = time.perf_counter()
    reranker = _get_reranker()
    pairs = [(query, doc.page_content) for doc in candidate_docs]
    scores = reranker.predict(pairs)
    rerank_time = time.perf_counter() - rerank_start

    ranked = sorted(
        zip(candidate_docs, scores),
        key=lambda x: float(x[1]),
        reverse=True,
    )
    top_docs = [doc for doc, _ in ranked[:top_k]]

    context_list: List[str] = []
    detailed_sources: List[Dict] = []

    for i, doc in enumerate(top_docs, start=1):
        raw_page = doc.metadata.get("page", 0)
        page_num = raw_page + 1 if isinstance(raw_page, int) else (raw_page or "?")
        source_file = str(
            doc.metadata.get("filename")
            or doc.metadata.get("source")
            or "Tài liệu"
        ).split("/")[-1]

        context_list.append(f"[Nguồn {i} | Trang {page_num}]: {doc.page_content}")
        detailed_sources.append(
            {
                "id": i,
                "page": page_num,
                "content": doc.page_content,
                "source_file": source_file,
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

    llm_start = time.perf_counter()
    response = llm.invoke(prompt)
    llm_time = time.perf_counter() - llm_start

    benchmark = {
        "retrieve_time_sec": round(retrieve_time, 3),
        "rerank_time_sec": round(rerank_time, 3),
        "llm_time_sec": round(llm_time, 3),
        "total_time_sec": round(time.perf_counter() - start_ts, 3),
        "candidate_count": len(candidate_docs),
        "returned_count": len(top_docs),
    }
    return response, detailed_sources, benchmark

import json
from typing import Dict, List, Tuple
import time

from langchain_community.llms import Ollama

from src.application.prompts import (
    get_rag_prompt,
    get_rag_prompt_with_history,
    get_self_rag_eval_prompt,
    get_self_rag_rewrite_prompt,
)


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


def _extract_json_payload(text: str) -> dict:
    if not text:
        return {}

    raw = text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        snippet = raw[start : end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            return {}

    return {}


def _retrieve_docs(vector_db, query: str, k: int = 5, fetch_k: int = 20):
    retriever = vector_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k, "fetch_k": fetch_k},
    )
    return retriever.invoke(query)


def _build_context_and_sources(docs) -> Tuple[str, List[Dict]]:
    context_list: List[str] = []
    sources: List[Dict] = []

    for i, doc in enumerate(docs, start=1):
        raw_page = doc.metadata.get("page", 0)
        page_num = raw_page + 1 if isinstance(raw_page, int) else (raw_page or "?")
        source_file = str(
            doc.metadata.get("filename")
            or doc.metadata.get("source")
            or "Tài liệu"
        ).split("/")[-1]

        context_list.append(f"[Nguồn {i} | Trang {page_num}]: {doc.page_content}")
        sources.append(
            {
                "id": i,
                "page": page_num,
                "content": doc.page_content,
                "source_file": source_file,
            }
        )

    return "\n\n".join(context_list), sources


def _answer_with_context(
    llm: Ollama,
    query: str,
    context_string: str,
    chat_history: List[Dict] | None = None,
) -> str:
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
    return llm.invoke(prompt)


def get_answer_with_selfrag_citation(
    query: str,
    vector_db,
    chat_history: List[Dict] | None = None,
    confidence_threshold: float = 0.62,
    initial_k: int = 5,
) -> Tuple[str, List[Dict], Dict]:
    start_ts = time.perf_counter()
    llm = Ollama(
        model="qwen2.5:7b",
        temperature=0.3,
        top_p=0.9,
        repeat_penalty=1.1,
    )

    docs = _retrieve_docs(vector_db=vector_db, query=query, k=initial_k)
    if not docs:
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
                "hops_used": 1,
                "confidence": 0.0,
                "rewritten_query": "",
                "total_time_sec": round(time.perf_counter() - start_ts, 3),
            },
        )

    context_string, sources = _build_context_and_sources(docs)
    answer = _answer_with_context(
        llm=llm,
        query=query,
        context_string=context_string,
        chat_history=chat_history,
    )

    eval_prompt = get_self_rag_eval_prompt().format(
        question=query,
        context=context_string,
        answer=answer,
    )
    eval_raw = llm.invoke(eval_prompt)
    eval_payload = _extract_json_payload(eval_raw)

    confidence = float(eval_payload.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))
    needs_rewrite = bool(eval_payload.get("needs_rewrite", False))
    rewritten_query = str(eval_payload.get("rewritten_query", "")).strip()

    should_retry = needs_rewrite or confidence < confidence_threshold
    hops_used = 1
    if should_retry:
        hops_used = 2
        if not rewritten_query:
            rewrite_prompt = get_self_rag_rewrite_prompt().format(
                question=query,
                chat_history=_format_chat_history(chat_history),
            )
            rewritten_query = str(llm.invoke(rewrite_prompt)).strip()

        if rewritten_query:
            docs_retry = _retrieve_docs(vector_db=vector_db, query=rewritten_query, k=initial_k)
            if docs_retry:
                context_hop2, sources_hop2 = _build_context_and_sources(docs_retry)
                answer_hop2 = _answer_with_context(
                    llm=llm,
                    query=rewritten_query,
                    context_string=context_hop2,
                    chat_history=chat_history,
                )

                synthesis_prompt = f"""
Bạn là SmartDoc AI. Hãy tổng hợp kết quả từ 2 hop truy xuất để trả lời câu hỏi gốc.

YÊU CẦU:
1. Trả lời dựa trên bằng chứng trong 2 context bên dưới.
2. Mỗi ý cần citation dạng [Nguồn X].
3. Nếu không đủ bằng chứng, nói rõ phần chưa đủ.

CÂU HỎI GỐC:
{query}

HOP 1 - CONTEXT:
{context_string}

HOP 1 - ANSWER:
{answer}

HOP 2 - REWRITTEN QUERY:
{rewritten_query}

HOP 2 - CONTEXT:
{context_hop2}

HOP 2 - ANSWER:
{answer_hop2}
"""
                answer = llm.invoke(synthesis_prompt)

                combined_sources = sources + sources_hop2
                renumbered_sources: List[Dict] = []
                for i, src in enumerate(combined_sources, start=1):
                    src_copy = dict(src)
                    src_copy["id"] = i
                    renumbered_sources.append(src_copy)
                sources = renumbered_sources

                eval_prompt_retry = get_self_rag_eval_prompt().format(
                    question=rewritten_query,
                    context=context_hop2,
                    answer=answer,
                )
                eval_retry_raw = llm.invoke(eval_prompt_retry)
                eval_retry_payload = _extract_json_payload(eval_retry_raw)
                confidence_retry = float(eval_retry_payload.get("confidence", confidence))
                confidence = max(0.0, min(1.0, confidence_retry))

    rewritten_suffix = f"\nQuery rewrite: {rewritten_query}" if rewritten_query else ""
    answer_with_confidence = (
        f"{answer}\n\n"
        f"(Self-RAG dùng {hops_used} hop | Độ tự tin: {confidence:.0%})"
        f"{rewritten_suffix}"
    )
    benchmark = {
        "hops_used": hops_used,
        "confidence": round(confidence, 3),
        "rewritten_query": rewritten_query,
        "total_time_sec": round(time.perf_counter() - start_ts, 3),
    }
    return answer_with_confidence, sources, benchmark

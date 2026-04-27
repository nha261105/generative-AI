from langchain_community.llms import Ollama
from typing import Tuple, List, Dict
from src.application.prompts import get_rag_prompt, get_rag_prompt_with_history


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


def get_answer_with_citation(
    query: str,
    vector_db,
    chat_history: List[Dict] | None = None,
) -> Tuple[str, List[Dict]]:
    # ===== 1. LLM =====
    llm = Ollama(
        model="qwen2.5:7b",
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
    )

    # ===== 2. Retriever =====
    retriever = vector_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3, "fetch_k": 10},
    )

    # ===== 3. Lấy docs =====
    relevant_docs = retriever.invoke(query)
    print(f">>Tìm thấy {len(relevant_docs)} đoạn tài liệu liên quan")

    if not relevant_docs:
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
        )

    context_list = []
    detailed_sources = []

    # # ===== 4. Build context + mapping =====
    for i, doc in enumerate(relevant_docs):
        source_id = i + 1
        raw_page = doc.metadata.get("page", 0)
        page_num = raw_page + 1 if isinstance(raw_page, int) else (raw_page or "?")
        content = doc.page_content
        source_file = str(
            doc.metadata.get("filename")
            or doc.metadata.get("source")
            or "Tài liệu"
        ).split("/")[-1]

        context_list.append(
            f"[Nguồn {source_id} | Trang {page_num}]: {content}"
        )

        detailed_sources.append({
            "id": source_id,
            "page": page_num,
            "content": content,
            "source_file": source_file,
        })

    context_string = "\n\n".join(context_list)

    # ===== 5. Prompt =====
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

    # ===== 6. LLM =====
    response = llm.invoke(prompt)

    return response, detailed_sources

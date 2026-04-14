from langchain_community.llms import Ollama
from typing import Tuple, List, Dict
from src.application.promts import get_rag_prompt

def get_answer_with_citation(query: str, vector_db) -> Tuple[str,List[Dict]]:
    # ===== 1. LLM =====
    llm = Ollama(
        model="qwen2.5:3b",
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
    context_list = []
    detailed_sources = []

    # # ===== 4. Build context + mapping =====
    for i,doc in enumerate(relevant_docs):
        source_id = i + 1
        page_num = doc.metadata.get("page",0) + 1
        content = doc.page_content

        context_list.append(
            f"[Nguồn {source_id} | Trang {page_num}]: {content}"
        )

        detailed_sources.append({
            "id": source_id,
            "page": page_num,
            "content": content,
            "source_file": doc.metadata.get("source", "N/A"),
        })

    context_string = "\n\n".join(context_list)

    # ===== 5. Prompt =====
    prompt = get_rag_prompt().format(
        context=context_string,
        question=query
    )

    # ===== 6. LLM =====
    response = llm.invoke(prompt)

    return response, detailed_sources

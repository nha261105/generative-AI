from langchain_community.llms import Ollama
from typing import Tuple, List, Dict
from langchain_core.prompts import ChatPromptTemplate

# Định nghĩa Template cho RAG
RAG_PROMPT_TEMPLATE = """
Bạn là SmartDoc AI - Một trợ lý phân tích tài liệu chuyên nghiệp. 
Hãy trả lời câu hỏi dựa TRỰC TIẾP trên các đoạn trích dẫn (Context) dưới đây. 

YÊU CẦU:
1. Mỗi ý trong câu trả lời PHẢI có citation dạng: [Nguồn X] được đặt ở cuối câu
2. X tương ứng với số nguồn trong Context (ví dụ: Nguồn 1, Nguồn 2,...)
3. Nếu thông tin không có trong tài liệu, hãy nói "Tôi không tìm thấy thông tin này trong tài liệu". 
4. Trả lời ngắn gọn, rõ ràng, bằng tiếng Việt
5. Luôn giữ thái độ khách quan.

---

QUY TẮC TRÍCH DẪN (BẮT BUỘC):
- Citation phải ở CUỐI câu
- Format đúng tuyệt đối: [Nguồn X]
- Không viết sai chính tả, không thêm ký tự

---

QUY TẮC NỘI DUNG:
- Trả lời ngắn gọn, rõ ràng
- Mỗi câu nên tương ứng với 1 nguồn
- Ưu tiên sử dụng lại từ ngữ trong Context (hạn chế paraphrase)

---

---
TÀI LIỆU TRÍCH XUẤT:
{context}
---

CÂU HỎI CỦA NGƯỜI DÙNG: {question}

TRẢ LỜI:
"""

def get_rag_prompt():
    return ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

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

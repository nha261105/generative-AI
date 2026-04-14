from langchain_community.llms import Ollama
from src.application.promts import get_rag_prompt

def get_answer(query: str, vector_db):
    """Hàm xử lý truy vấn RAG"""
    
    # 1. Kết nối với Ollama (Model Layer)
    llm = Ollama(
        model="qwen2.5:3b",
        temperature=0.7,    #Creativity level
        top_p=0.9,          #Nucleus sampling
        repeat_penalty=1.1, #Avoid repetition
        # base_url="http://127.0.0.1:11434"
    )
    
    # 2. Thiết lập Retriever (Tìm kiếm top 3 đoạn liên quan nhất)
    retriever = vector_db.as_retriever(
        search_type="similarity",  # Or " mmr " for diverse results
        search_kwargs={
            "k": 3,         # Number of chunks to return
            "fetch_k": 10,  # Fetch more then filter
            }
    )
    
    # 3. Truy xuất tài liệu liên quan
    relevant_docs = retriever.invoke(query)

    print(f">>Tìm thấy {len(relevant_docs)} đoạn tài liệu liên quan")
    
    # 4. Chuẩn bị Context từ tài liệu tìm được
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    # 5. Lấy danh sách trang nguồn (Metadata)
    sources = list(set([f"Trang {doc.metadata.get('page', 0) + 1}" for doc in relevant_docs]))

    print(">>> Đang gửi câu hỏi sang Ollama (Qwen2.5)...")
    
    # 6. Tạo Prompt và gọi LLM
    prompt = get_rag_prompt().format(context=context, question=query)
    response = llm.invoke(prompt)

    print(">>> Ollama đã trả lời xong!")
    
    return response, sources
from langchain_community.llms import Ollama
from src.application.promts import get_rag_prompt
from src.application.chain_hybrid import create_hybrid_retriever
import time
def get_answer(query: str, vector_db, chunks):
    """Hàm xử lý truy vấn RAG"""
    
    # 1. Kết nối với Ollama (Model Layer)
    llm = Ollama(
        model="qwen2.5:7b",
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

    hybrid_retriever = create_hybrid_retriever(
    vector_db,
    chunks
    )
    
    # 3. Truy xuất tài liệu liên quan
    #3.1 pure vector search
    relevant_docs = retriever.invoke(query)
    #3.2 hybrid search
    hybrid_relevant_docs = hybrid_retriever.invoke(query)

    print(f">>Tìm thấy {len(relevant_docs)} đoạn tài liệu liên quan")
    print(f">>Hybrid tìm thấy {len(hybrid_relevant_docs)} đoạn tài liệu liên quan")

    #3.3 time
    #3.3.1 pure vector time
    start = time.perf_counter()
    relevant_docs = retriever.invoke(query)
    vector_time = time.perf_counter() - start

    #3.3.2 hybrid time
    start = time.perf_counter()
    hybrid_relevant_docs = hybrid_retriever.invoke(query)
    hybrid_time = time.perf_counter() - start

    print("\n=== PERFORMANCE COMPARISON ===")
    print(f">>Vector time : {vector_time:.4f}s")
    print(f">>Hybrid time : {hybrid_time:.4f}s")
    print(f">>Difference  : {(hybrid_time-vector_time):.4f}s")
    print(f">>VECTOR tìm thấy {len(relevant_docs)} đoạn")
    print(f">>HYBRID tìm thấy {len(hybrid_relevant_docs)} đoạn")
    
    # 4. Chuẩn bị Context từ tài liệu tìm được
    #4.1 pure vector context
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    #4.2 hybrid context
    hybrid_context = "\n\n".join([doc.page_content for doc in hybrid_relevant_docs])

    # 5. Lấy danh sách trang nguồn (Metadata)
    #5.1 pure vector sources
    sources = sorted(set(
        f"Trang {doc.metadata.get('page',0)+1}"for doc in relevant_docs))
    #5.2 hybrid sources
    hybrid_sources = sorted(set(
        f"Trang {doc.metadata.get('page',0)+1}"for doc in hybrid_relevant_docs))

    print(">>> Đang gửi câu hỏi sang Ollama (Qwen2.5)...")
    
    # 6. Tạo Prompt và gọi LLM
    #6.1 pure vector prompt
    prompt = get_rag_prompt().format(context=context, question=query)
    response = llm.invoke(prompt)
    #6.2 hybrid prompt
    hybrid_prompt = get_rag_prompt().format(context=hybrid_context, question=query)
    hybrid_response = llm.invoke(hybrid_prompt)

    print(">>> Ollama đã trả lời xong!")
    
    return response, sources, hybrid_response, hybrid_sources
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage, AIMessage

#Prompts

# Prompt 1: Dùng để viết lại câu hỏi dựa trên ngữ cảnh lịch sử
CONTEXTUALIZE_Q_SYSTEM_PROMPT = """Cho lịch sử trò chuyện và câu hỏi mới nhất của người dùng.
Câu hỏi này có thể tham chiếu đến ngữ cảnh trong lịch sử trò chuyện (ví dụ: dùng các từ 'nó', 'vậy còn...', 'tại sao lại thế').
Hãy tạo ra một câu hỏi độc lập (standalone question) có thể hiểu được mà không cần lịch sử trò chuyện.
TUYỆT ĐỐI KHÔNG trả lời câu hỏi, chỉ định dạng lại nó. Nếu câu hỏi đã rõ ràng, hãy trả về nguyên bản."""

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"), # Chèn lịch sử vào đây
    ("human", "{input}"),
])

# Prompt 2: Prompt RAG chính (Đã bao gồm luật trích dẫn [Nguồn X])
QA_SYSTEM_PROMPT = """Bạn là SmartDoc AI - Chuyên gia phân tích dữ liệu.
Nhiệm vụ: Trả lời câu hỏi dựa trên Context được cung cấp và Lịch sử trò chuyện.

---
QUY TẮC BẮT BUỘC:
1. ĐỊNH DẠNG TRÍCH DẪN: Chỉ sử dụng thẻ `[Nguồn X]`. Gắn ở cuối mỗi câu khẳng định.
2. CHÍNH XÁC: Chỉ dùng dữ liệu có trong Context. Không tự suy diễn.
3. FOLLOW-UP: Bạn có thể tham chiếu lại những gì đã nói trong lịch sử trò chuyện nếu người dùng hỏi tiếp nối.

---
TÀI LIỆU TRÍCH XUẤT (CONTEXT):
{context}"""

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", QA_SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


#KHỞI TẠO CHUỖI CONVERSATIONAL RAG

def get_conversational_chain(vector_db):
    """
    Tạo chain RAG có khả năng xử lý lịch sử hội thoại
    """
    # 1. Khởi tạo LLM (Dùng Qwen 2.5 7B hoặc 3B tùy phần cứng)
    llm = Ollama(
        model="qwen2.5:7b", 
        temperature=0.1,
    )

    # 2. Khởi tạo Retriever
    retriever = vector_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3, "fetch_k": 10},
    )

    # 3. Tạo chuỗi nhận biết lịch sử để xử lý follow-up questions
    history_aware_retriever = create_history_aware_retriever(llm,retriever,contextualize_q_prompt)

    # 4. Tạo chuỗi Trả lời câu hỏi (QA Chain). Đọc context trả ra câu trả lời có trích dẫn 
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # 5. Kết hợp lại thành chain hoàn chỉnh 
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return rag_chain

def get_answer_with_memory(query: str, chat_history: list, vector_db) -> dict:
    """
    Hàm thực thi chính trả về câu trả lời và danh sách nguồn
    - chat_history: Mảng các object HumanMessage và AIMessage
    """

    rag_chain = get_conversational_chain(vector_db)

    response = rag_chain.invoke({
        "input": query,
        "chat_history": chat_history        
    })

    detailed_sources = []

    for i,doc in enumerate(response["context"]):
        source_id = i + 1

        detailed_sources.append({
            "id": source_id,
            "page": doc.metadata.get("page", 0) + 1,
            "content": doc.page_content.strip(),
            "source_file": doc.metadata.get("source", "N/A"),            
        })

    return {
        "answer": response["answer"],
        "sources": detailed_sources
    }
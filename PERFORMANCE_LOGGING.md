# Performance Logging Guide

## Tổng quan

Hệ thống đã được cập nhật với performance logging chi tiết để giúp xác định bottleneck trong RAG pipeline.

## Các điểm tracking

### 1. Model Loading
- **Embedding Model Load**: Thời gian load sentence-transformers model (~5-10s lần đầu)
- **LLM Load**: Thời gian khởi tạo Ollama connection (~0.1-0.5s)

### 2. Query Processing
- **Query Embedding**: Thời gian embed câu hỏi thành vector (~0.1-0.3s)
- **Retriever Creation**: Thời gian tạo retriever object (~0.01s)
- **Retriever Invoke**: Thời gian embedding + FAISS search (~0.2-1s)

### 3. Context Building
- **Context Building**: Thời gian format documents thành context string (~0.01-0.05s)
- **Prompt Formatting**: Thời gian format prompt template (~0.001s)

### 4. LLM Generation
- **LLM Invoke**: Thời gian gọi LLM để generate answer (có thể rất lâu: 30-150s)

### 5. Advanced Features
- **Query Rewrite**: Nếu có conversational rewrite (~2-5s)
- **Re-rank**: Nếu dùng CrossEncoder (~0.5-2s)
- **Self-RAG**: Nếu dùng Self-RAG với multiple hops (~10-30s)

## Output mẫu

```
============================================================
Processing Query: tên của người này là gì ?
============================================================
  📦 Loading embedding model...
  ⏱️  Embedding model loaded: 6.234s
  🔍 Starting semantic search + LLM...
  ⏱️  Retriever creation: 0.012s
  ⏱️  Query embedding: 0.156s
  ⏱️  Retrieval invoke: 0.234s (3 docs)
  ⏱️  Context building: 0.023s
  ⏱️  Prompt formatting: 0.001s
  📦 Loading LLM (temp=0.7)...
  ⏱️  LLM loaded: 0.234s
  ⏱️  LLM invoke: 142.567s
  ⏱️  Semantic search + LLM: 143.012s

============================================================
PERFORMANCE SUMMARY
============================================================
LLM Calls: 1
Total Time: 149.478s

Detailed Time Breakdown:
  • LLM Load: 0.234s
  • Retrieval Total: 0.234s
    - Invoke (embed + search): 0.234s
  • Context Building: 0.023s
  • Generation Total: 142.567s
    - LLM Invoke: 142.567s

Pipeline: semantic → llm
============================================================
```

## Phân tích bottleneck

### Nếu thời gian chậm ở:

1. **Embedding Model Load (6-10s)**
   - Chỉ xảy ra lần đầu tiên
   - Sau đó được cache bởi Streamlit
   - Không thể tối ưu nhiều

2. **Query Embedding (>1s)**
   - Model quá nặng
   - Xem xét dùng model nhẹ hơn
   - Hoặc GPU acceleration

3. **Retrieval Invoke (>2s)**
   - FAISS index quá lớn
   - Xem xét giảm số documents
   - Hoặc optimize FAISS parameters

4. **LLM Invoke (>100s)** ⚠️ **BOTTLENECK CHÍNH**
   - Ollama model inference chậm
   - Giải pháp:
     - Dùng model nhỏ hơn (qwen2.5:3b thay vì 7b)
     - Dùng GPU nếu có
     - Giảm context length
     - Dùng API service (OpenAI, Anthropic) thay vì local

## Cách sử dụng

Logging tự động chạy khi bạn submit query trong Streamlit app. Xem terminal để thấy output chi tiết.

### Tắt logging (nếu cần)

Để tắt logging chi tiết, comment các dòng `print()` trong:
- `src/utils/logger.py`
- `src/application/rag_strategies.py`
- `src/application/chain_citation.py`
- `src/application/chain_base.py`
- `src/model_layer/cache.py`
- `src/data_layer/embeddings.py`

## Khuyến nghị tối ưu

Dựa trên log của bạn (174s total), vấn đề chính là **LLM inference**:

1. **Ngắn hạn**:
   - Giảm số documents retrieve (k=3 → k=2)
   - Giảm chunk_size để context ngắn hơn
   - Dùng model nhỏ hơn

2. **Dài hạn**:
   - Setup GPU cho Ollama
   - Chuyển sang API service
   - Implement streaming response
   - Cache LLM responses (đã có trong code)

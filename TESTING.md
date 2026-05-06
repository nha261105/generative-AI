# Testing Guide - SmartDoc AI RAG System

## Tổng quan

File này hướng dẫn test 4 features chính của hệ thống RAG với các test cases cụ thể.

## Setup Test Environment

### 1. Chuẩn bị dữ liệu test

Đặt các file PDF test vào thư mục `data/documents/`:
- ✅ `Smart School Bus Tracking System.pdf` - Tài liệu kỹ thuật
- ✅ `Bản sao của Chương 3.pdf` - Tài liệu học thuật
- ✅ `antigravity&cloud_research.pdf` - Tài liệu nghiên cứu
- ✅ `TestPDF_RAG.pdf` - Tài liệu test
- ✅ `nguyen-hoang-minh-an_4063329_1110165a9b5c3441_4063329.pdf` - CV tiếng Việt

### 2. Khởi động ứng dụng

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows

# Chạy Streamlit app
streamlit run app.py
```

### 3. Upload tài liệu

1. Mở sidebar trong Streamlit app
2. Upload các file PDF từ `data/documents/`
3. Đợi indexing hoàn tất (xem terminal log)

---

## Feature 1: Base RAG (Semantic Search)

### Mục đích
Test khả năng tìm kiếm ngữ nghĩa cơ bản và trả lời câu hỏi factoid đơn giản.

### Cấu hình
- **Search Mode**: Semantic
- **Re-rank**: OFF
- **Self-RAG**: OFF
- **Conversational**: OFF (clear chat history)

### Test Cases

#### TC1.1: Factoid Question - Thông tin trực tiếp
**Input:**
```
Hệ thống Smart School Bus Tracking System có những tính năng chính nào?
```

**Expected Output:**
- ✅ Trả lời liệt kê các tính năng chính
- ✅ Trích dẫn từ file "Smart School Bus Tracking System.pdf"
- ✅ Có source citation với page number
- ✅ Thời gian response: < 30s (sau khi model đã load)

**Đánh giá:**
- [ ] Câu trả lời chính xác
- [ ] Có citation đầy đủ
- [ ] Không hallucination
- [ ] Performance chấp nhận được

---

#### TC1.2: Simple Fact Extraction
**Input:**
```
Tên của người trong CV là gì?
```
(Test với file CV tiếng Việt)

**Expected Output:**
- ✅ Trả về tên chính xác từ CV
- ✅ Không bịa thêm thông tin
- ✅ Citation từ file CV

**Đánh giá:**
- [ ] Tên chính xác 100%
- [ ] Không thêm thông tin không có trong CV
- [ ] Source tracking đúng

---

#### TC1.3: Concept Definition
**Input:**
```
Cloud computing là gì theo tài liệu antigravity&cloud_research?
```

**Expected Output:**
- ✅ Định nghĩa cloud computing từ tài liệu
- ✅ Bám sát nội dung gốc
- ✅ Citation rõ ràng

**Đánh giá:**
- [ ] Định nghĩa chính xác
- [ ] Không trộn lẫn với kiến thức chung
- [ ] Source từ đúng file

---

#### TC1.4: Negative Test - Không có thông tin
**Input:**
```
Giá cổ phiếu của Tesla hôm nay là bao nhiêu?
```

**Expected Output:**
- ✅ Từ chối trả lời lịch sự
- ✅ Giải thích không tìm thấy thông tin trong tài liệu
- ✅ KHÔNG bịa số liệu

**Đánh giá:**
- [ ] Không hallucination
- [ ] Thông báo rõ ràng
- [ ] Gợi ý upload thêm tài liệu

---

## Feature 2: Self-RAG (Advanced RAG)

### Mục đích
Test khả năng tự đánh giá, query rewriting, multi-hop reasoning, và confidence scoring.

### Cấu hình
- **Search Mode**: Semantic
- **Re-rank**: ON
- **Self-RAG**: ON
- **Conversational**: OFF

### Test Cases

#### TC2.1: Query Rewriting - Câu hỏi mơ hồ
**Input:**
```
Cái hệ thống bus đó hoạt động như thế nào?
```
(Câu hỏi mơ hồ, thiếu context)

**Expected Output:**
- ✅ Hệ thống tự viết lại query rõ ràng hơn
- ✅ Trả lời về Smart School Bus Tracking System
- ✅ Có confidence score
- ✅ Log hiển thị "Query Rewrite: Triggered"

**Đánh giá:**
- [ ] Query được rewrite
- [ ] Câu trả lời chính xác
- [ ] Confidence score hiển thị
- [ ] Xem terminal log để verify rewrite

---

#### TC2.2: Multi-hop Reasoning - So sánh
**Input:**
```
So sánh ưu điểm và nhược điểm của cloud computing và edge computing trong tài liệu?
```

**Expected Output:**
- ✅ Tìm thông tin từ nhiều đoạn văn khác nhau
- ✅ Tổng hợp và so sánh
- ✅ Confidence score cao (>70%)
- ✅ Có thể có 2 hops (xem log)

**Đánh giá:**
- [ ] So sánh đầy đủ cả 2 khái niệm
- [ ] Thông tin từ nhiều nguồn
- [ ] Confidence score hợp lý
- [ ] Hops used: 1 hoặc 2

---

#### TC2.3: Low Confidence - Thông tin không đủ
**Input:**
```
Phân tích chi tiết kiến trúc microservices của hệ thống Smart Bus?
```
(Có thể tài liệu không có chi tiết về microservices)

**Expected Output:**
- ✅ Confidence score thấp (<60%)
- ✅ Có thể trigger hop 2 để tìm thêm
- ✅ Thừa nhận nếu không đủ thông tin
- ✅ Không bịa thêm

**Đánh giá:**
- [ ] Confidence score phản ánh đúng
- [ ] Không hallucination
- [ ] Thông báo rõ ràng nếu thiếu info

---

#### TC2.4: Re-ranking Effect
**Input:**
```
GPS tracking trong Smart School Bus System hoạt động ra sao?
```

**Expected Output:**
- ✅ Retrieve 8 docs ban đầu
- ✅ Re-rank xuống còn 5 docs tốt nhất
- ✅ Câu trả lời chính xác hơn Base RAG
- ✅ Xem terminal log để verify re-ranking scores

**Đánh giá:**
- [ ] Pre-rerank: 8 docs
- [ ] Post-rerank: 5 docs
- [ ] Scores giảm dần
- [ ] Câu trả lời chất lượng cao

---

## Feature 3: Hybrid Search

### Mục đích
Test khả năng kết hợp semantic search + keyword search (BM25).

### Cấu hình
- **Search Mode**: Hybrid
- **Re-rank**: OFF (test thuần hybrid)
- **Self-RAG**: OFF
- **Conversational**: OFF

### Test Cases

#### TC3.1: Technical Term - Thuật ngữ chuyên ngành
**Input:**
```
GPS module trong tài liệu là loại nào?
```

**Expected Output:**
- ✅ Bắt chính xác từ khóa "GPS module"
- ✅ Kết hợp semantic + keyword matching
- ✅ Trả về thông tin kỹ thuật chính xác

**Đánh giá:**
- [ ] Tìm đúng đoạn chứa "GPS module"
- [ ] Không bỏ sót do semantic search
- [ ] Thông tin kỹ thuật chính xác

---

#### TC3.2: Acronym Search - Tìm viết tắt
**Input:**
```
IoT được sử dụng như thế nào trong hệ thống?
```

**Expected Output:**
- ✅ Bắt được từ viết tắt "IoT"
- ✅ Không nhầm với các từ tương tự ngữ nghĩa
- ✅ Hybrid search vượt trội semantic

**Đánh giá:**
- [ ] Tìm chính xác "IoT"
- [ ] Không bị nhiễu bởi từ đồng nghĩa
- [ ] Performance tốt

---

#### TC3.3: Code/ID Search - Mã số, ID
**Input:**
```
Tìm thông tin về module ESP32 trong tài liệu
```

**Expected Output:**
- ✅ Keyword "ESP32" được match chính xác
- ✅ BM25 component hoạt động
- ✅ Không bỏ sót do vector search

**Đánh giá:**
- [ ] Tìm đúng "ESP32"
- [ ] Hybrid tốt hơn semantic only
- [ ] Citation chính xác

---

#### TC3.4: Comparison - Hybrid vs Semantic
**Test song song cùng query với 2 modes**

**Input (Semantic):**
```
Hệ thống sử dụng công nghệ gì để theo dõi vị trí?
```

**Input (Hybrid):**
```
Hệ thống sử dụng công nghệ gì để theo dõi vị trí?
```

**Expected:**
- ✅ Hybrid trả về kết quả chi tiết hơn
- ✅ Hybrid bắt được các thuật ngữ kỹ thuật
- ✅ Semantic có thể bỏ sót một số chi tiết

**Đánh giá:**
- [ ] So sánh 2 kết quả
- [ ] Ghi nhận sự khác biệt
- [ ] Hybrid có lợi thế với technical docs

---

## Feature 4: Conversational RAG

### Mục đích
Test khả năng duy trì context qua nhiều lượt hội thoại.

### Cấu hình
- **Search Mode**: Semantic hoặc Hybrid
- **Re-rank**: Optional
- **Self-RAG**: Optional
- **Conversational**: ON (KHÔNG clear chat history)

### Test Cases

#### TC4.1: Follow-up Question - Câu hỏi tiếp theo
**Conversation Flow:**

**Turn 1:**
```
Smart School Bus Tracking System là gì?
```
**Expected:** Giới thiệu tổng quan về hệ thống

**Turn 2:**
```
Nó có những tính năng gì?
```
**Expected:** 
- ✅ Hiểu "nó" = Smart School Bus Tracking System
- ✅ Liệt kê tính năng
- ✅ Không hỏi lại "nó là gì?"

**Turn 3:**
```
Vậy công nghệ nào được sử dụng?
```
**Expected:**
- ✅ Vẫn trong context của Smart Bus System
- ✅ Trả lời về công nghệ của hệ thống đó

**Đánh giá:**
- [ ] Context được duy trì qua 3 turns
- [ ] Đại từ được resolve đúng
- [ ] Không lặp lại thông tin đã nói

---

#### TC4.2: Pronoun Resolution - Giải quyết đại từ
**Conversation Flow:**

**Turn 1:**
```
Cloud computing có ưu điểm gì?
```
**Expected:** Liệt kê ưu điểm cloud computing

**Turn 2:**
```
Còn nhược điểm của nó thì sao?
```
**Expected:**
- ✅ "nó" = cloud computing
- ✅ Liệt kê nhược điểm
- ✅ Query rewrite log: "Nhược điểm của cloud computing là gì?"

**Đánh giá:**
- [ ] Pronoun resolution chính xác
- [ ] Xem log để verify query rewrite
- [ ] Câu trả lời liên quan đúng topic

---

#### TC4.3: Topic Switching - Chuyển đề
**Conversation Flow:**

**Turn 1:**
```
GPS tracking hoạt động như thế nào?
```
**Expected:** Giải thích GPS tracking

**Turn 2:**
```
Còn về cloud computing thì sao?
```
**Expected:**
- ✅ Nhận biết chuyển topic
- ✅ Trả lời về cloud computing
- ✅ KHÔNG còn nói về GPS

**Turn 3:**
```
Quay lại vấn đề GPS, độ chính xác của nó là bao nhiêu?
```
**Expected:**
- ✅ Quay lại topic GPS
- ✅ Trả lời về độ chính xác

**Đánh giá:**
- [ ] Topic switching hoạt động
- [ ] Context được quản lý đúng
- [ ] Không bị nhầm lẫn giữa các topic

---

#### TC4.4: Long Conversation - Hội thoại dài
**Test với 5+ turns liên tiếp**

**Expected:**
- ✅ Chỉ giữ 2-3 turns gần nhất (theo config max_turns=2)
- ✅ Không bị quá tải context
- ✅ Vẫn trả lời chính xác

**Đánh giá:**
- [ ] Performance ổn định qua nhiều turns
- [ ] Memory management tốt
- [ ] Không bị degradation

---

## Performance Benchmarks

### Thời gian chấp nhận được

| Operation | First Time | Cached | Target |
|-----------|-----------|--------|--------|
| Model Load | 5-10s | <0.5s | N/A |
| Query Embedding | 0.1-0.3s | 0.1-0.3s | <0.5s |
| Retrieval | 0.2-1s | 0.2-1s | <2s |
| LLM Generation | 30-150s | 30-150s | <60s* |
| Total (Base RAG) | 40-160s | 35-155s | <70s* |
| Total (Self-RAG) | 50-180s | 45-175s | <90s* |

*Phụ thuộc vào hardware và LLM model size

### Metrics cần track

1. **Accuracy**: Câu trả lời có chính xác không?
2. **Relevance**: Có bám sát tài liệu không?
3. **Citation**: Source tracking có đầy đủ không?
4. **Hallucination**: Có bịa thông tin không?
5. **Performance**: Thời gian response có chấp nhận được không?

---

## Test Execution Checklist

### Trước khi test
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Ollama running (check: `ollama list`)
- [ ] Test PDFs in `data/documents/`
- [ ] Streamlit app running
- [ ] Documents uploaded và indexed

### Trong khi test
- [ ] Ghi chú kết quả từng test case
- [ ] Screenshot nếu cần
- [ ] Copy terminal logs
- [ ] So sánh với expected output
- [ ] Đánh dấu Pass/Fail

### Sau khi test
- [ ] Tổng hợp kết quả
- [ ] Identify bugs/issues
- [ ] Document edge cases
- [ ] Suggest improvements

---

## Test Results Template

```markdown
## Test Run: [Date]

### Environment
- OS: [Linux/Windows/Mac]
- Python: [version]
- LLM Model: [qwen2.5:7b]
- Hardware: [CPU/GPU specs]

### Feature 1: Base RAG
- TC1.1: ✅ PASS / ❌ FAIL - [Notes]
- TC1.2: ✅ PASS / ❌ FAIL - [Notes]
- TC1.3: ✅ PASS / ❌ FAIL - [Notes]
- TC1.4: ✅ PASS / ❌ FAIL - [Notes]

### Feature 2: Self-RAG
- TC2.1: ✅ PASS / ❌ FAIL - [Notes]
- TC2.2: ✅ PASS / ❌ FAIL - [Notes]
- TC2.3: ✅ PASS / ❌ FAIL - [Notes]
- TC2.4: ✅ PASS / ❌ FAIL - [Notes]

### Feature 3: Hybrid Search
- TC3.1: ✅ PASS / ❌ FAIL - [Notes]
- TC3.2: ✅ PASS / ❌ FAIL - [Notes]
- TC3.3: ✅ PASS / ❌ FAIL - [Notes]
- TC3.4: ✅ PASS / ❌ FAIL - [Notes]

### Feature 4: Conversational RAG
- TC4.1: ✅ PASS / ❌ FAIL - [Notes]
- TC4.2: ✅ PASS / ❌ FAIL - [Notes]
- TC4.3: ✅ PASS / ❌ FAIL - [Notes]
- TC4.4: ✅ PASS / ❌ FAIL - [Notes]

### Overall Summary
- Total Tests: 16
- Passed: X
- Failed: Y
- Pass Rate: Z%

### Issues Found
1. [Issue description]
2. [Issue description]

### Recommendations
1. [Recommendation]
2. [Recommendation]
```

---

## Advanced Testing (Optional)

### Stress Testing
- Upload 10+ PDFs cùng lúc
- Test với documents lớn (>100 pages)
- Concurrent queries

### Edge Cases
- Empty PDF
- Scanned PDF (no text)
- Non-English documents
- Mixed language documents
- Very long queries (>500 chars)
- Special characters in queries

### Integration Testing
- Test all features combined
- Self-RAG + Hybrid + Conversational
- Performance under load

---

## Troubleshooting

### Common Issues

**Issue 1: LLM quá chậm (>150s)**
- Solution: Dùng model nhỏ hơn (qwen2.5:3b)
- Solution: Enable GPU
- Solution: Giảm context length

**Issue 2: Hallucination**
- Check: Self-RAG có bật không?
- Check: Confidence score thấp?
- Solution: Tăng k retrieval
- Solution: Improve prompt

**Issue 3: Conversational không nhớ context**
- Check: Chat history có được pass không?
- Check: max_turns setting
- Check: Query rewrite có trigger không?

**Issue 4: Hybrid search không khác biệt**
- Check: BM25 retriever có hoạt động không?
- Check: Documents có được index đúng không?
- Test với technical terms rõ ràng

---

## Next Steps

Sau khi hoàn thành testing:

1. **Document findings** trong test results
2. **Prioritize bugs** theo severity
3. **Optimize performance** dựa trên bottlenecks
4. **Improve prompts** nếu cần
5. **Add more test cases** cho edge cases
6. **Automate testing** nếu có thời gian

---

## Contact & Support

Nếu gặp vấn đề trong quá trình test, check:
- Terminal logs (performance tracking)
- Streamlit debug info
- FAISS index integrity
- Ollama model status

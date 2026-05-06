# Testing Summary - SmartDoc AI

## ✅ Đã hoàn thành

Hệ thống testing đã được setup đầy đủ với:

### 📄 Documentation (5 files)
1. **TESTING.md** - Full testing guide với 16 test cases chi tiết
2. **TESTING_QUICK_GUIDE.md** - Quick reference 5 phút
3. **TESTING_README.md** - Tổng quan và workflow
4. **test_checklist.md** - Checklist để track progress
5. **TESTING_SUMMARY.md** - File này

### 🔧 Scripts (3 files)
1. **prepare_test_data.py** - Kiểm tra môi trường test
2. **run_tests.py** - Automated testing với manual evaluation
3. **test_performance_logging.py** - Performance testing

### 📊 Test Coverage

| Feature | Test Cases | Status |
|---------|-----------|--------|
| Base RAG | 4 | ✅ Ready |
| Self-RAG | 4 | ✅ Ready |
| Hybrid Search | 4 | ✅ Ready |
| Conversational | 4 | ✅ Ready |
| **RAG vs GraphRAG** | **4** | **✅ Ready** |
| **Total** | **20** | **✅ Complete** |

---

## 🎯 Cách sử dụng

### Option 1: Quick Test (5 phút)
```bash
# 1. Kiểm tra môi trường
python3 prepare_test_data.py

# 2. Đọc quick guide
cat TESTING_QUICK_GUIDE.md

# 3. Test trong Streamlit app
streamlit run app.py
```

### Option 2: Automated Test (15-30 phút)
```bash
# Chạy automated test suite
python3 run_tests.py

# Sẽ tạo report tự động: test_results_YYYYMMDD_HHMMSS.txt
```

### Option 3: Full Manual Test (1-2 giờ)
```bash
# 1. Đọc full guide
cat TESTING.md

# 2. Dùng checklist
cat test_checklist.md

# 3. Test từng feature chi tiết
# 4. Document kết quả
```

---

## 📋 Test Cases Overview

### Feature 1: Base RAG (Semantic Search)
```
TC1.1: Factoid Question
  Query: "Hệ thống Smart School Bus có tính năng gì?"
  Check: Accuracy, Citation, No hallucination

TC1.2: Fact Extraction
  Query: "Tên của người trong CV là gì?"
  Check: Exact match, No extra info

TC1.3: Concept Definition
  Query: "Cloud computing là gì theo tài liệu?"
  Check: Definition accuracy, Source tracking

TC1.4: Negative Test
  Query: "Giá cổ phiếu Tesla hôm nay?"
  Check: Refuse to answer, No hallucination
```

### Feature 2: Self-RAG (Advanced)
```
TC2.1: Query Rewriting
  Query: "Cái hệ thống bus đó hoạt động thế nào?"
  Check: Query rewrite triggered, Confidence score

TC2.2: Multi-hop Reasoning
  Query: "So sánh cloud vs edge computing?"
  Check: Multi-source synthesis, High confidence

TC2.3: Low Confidence
  Query: "Phân tích microservices của Smart Bus?"
  Check: Low confidence if insufficient info

TC2.4: Re-ranking Effect
  Query: "GPS tracking hoạt động ra sao?"
  Check: 8 docs → 5 docs, Better quality
```

### Feature 3: Hybrid Search
```
TC3.1: Technical Term
  Query: "GPS module là loại nào?"
  Check: Exact keyword match

TC3.2: Acronym Search
  Query: "IoT được dùng như thế nào?"
  Check: Acronym matching

TC3.3: Code/ID Search
  Query: "Thông tin về ESP32?"
  Check: Technical ID matching

TC3.4: Comparison
  Query: Same query in Semantic vs Hybrid
  Check: Hybrid better for technical docs
```

### Feature 4: Conversational RAG
```
TC4.1: Follow-up Question
  Turn 1: "Smart Bus System là gì?"
  Turn 2: "Nó có tính năng gì?"
  Turn 3: "Công nghệ nào được dùng?"
  Check: Context maintained across turns

TC4.2: Pronoun Resolution
  Turn 1: "Cloud computing có ưu điểm gì?"
  Turn 2: "Còn nhược điểm của nó?"
  Check: "nó" = cloud computing

TC4.3: Topic Switching
  Turn 1: "GPS tracking hoạt động thế nào?"
  Turn 2: "Còn về cloud computing?"
  Turn 3: "Quay lại GPS, độ chính xác?"
  Check: Topic switch handling

TC4.4: Long Conversation
  Test: 5+ turns
  Check: Memory management, No degradation
```

### Feature 5: RAG vs GraphRAG Comparison ⚡
```
TC5.1: Global Summary Question
  Query: "Tóm tắt toàn bộ nội dung chính trong tài liệu"
  Method: Click "⚡ Compare with GraphRAG" button
  Check: 
    - GraphRAG: Bao quát toàn cục, nhiều khía cạnh
    - RAG: Chỉ thấy vài đoạn ngẫu nhiên
    - GraphRAG tốt hơn cho overview questions

TC5.2: Multi-hop Connection
  Query: "Mối liên hệ giữa các công nghệ trong tài liệu?"
  Method: Click "⚡ Compare with GraphRAG" button
  Check:
    - GraphRAG: Traverse graph, tìm connections
    - RAG: Semantic search, isolated chunks
    - GraphRAG hiểu relationships tốt hơn

TC5.3: Entity Relationship
  Query: "Các thành phần của hệ thống liên kết thế nào?"
  Method: Click "⚡ Compare with GraphRAG" button
  Check:
    - GraphRAG: 2-hop traversal, expand context
    - RAG: Top-K similarity only
    - Source overlap: Thường < 50%

TC5.4: Performance & Quality Comparison
  Query: Any complex question
  Method: Click "⚡ Compare with GraphRAG" button
  Metrics to check:
    - Time: RAG vs GraphRAG (parallel execution)
    - Sources: Number of documents used
    - Overlap: Common sources between methods
    - Quality: Completeness, coherence
    - Graph stats: Nodes, edges, expansion
```

### Feature 5: RAG vs GraphRAG Comparison
```
TC5.1: Global Summary Question
  Query: "Tóm tắt toàn bộ nội dung chính trong tài liệu"
  Check: GraphRAG bao quát hơn, RAG chỉ thấy vài đoạn

TC5.2: Multi-hop Connection
  Query: "Mối liên hệ giữa các công nghệ trong tài liệu?"
  Check: GraphRAG traverse graph, RAG chỉ semantic

TC5.3: Entity Relationship
  Query: "Các thành phần của hệ thống liên kết thế nào?"
  Check: GraphRAG hiểu relationships, RAG isolated

TC5.4: Performance Comparison
  Query: Same query for both
  Check: Time, sources, overlap, quality
```

---

## 🎬 Quick Start Demo

### 1. Kiểm tra môi trường
```bash
$ python3 prepare_test_data.py

✓ Test Documents: 5 PDFs found
✓ Ollama: qwen2.5:7b running
✓ FAISS Indexes: 5 indexes ready
```

### 2. Test một feature nhanh
```bash
# Start app
$ streamlit run app.py

# In browser:
1. Config: Semantic | Re-rank OFF | Self-RAG OFF
2. Query: "Hệ thống Smart School Bus có tính năng gì?"
3. Check response có citation và chính xác
```

### 3. Test GraphRAG Comparison ⚡
```bash
# In browser (sau khi có câu trả lời):
1. Click button "⚡ Compare with GraphRAG"
2. Đợi parallel execution (RAG + GraphRAG chạy song song)
3. Xem side-by-side comparison:
   - Left: RAG answer
   - Right: GraphRAG answer
   - Stats: Time, sources, overlap
4. So sánh chất lượng:
   - GraphRAG: Bao quát, toàn cục, nhiều connections
   - RAG: Cụ thể, focused, semantic similarity
```

### 4. Xem performance logs
```
Terminal output:
============================================================
Processing Query: Hệ thống Smart School Bus có tính năng gì?
============================================================
  🔍 Starting semantic search + LLM...
  ⏱️  Retriever creation: 0.012s
  ⏱️  Query embedding: 0.156s
  ⏱️  Retrieval invoke: 0.234s (3 docs)
  ⏱️  Context building: 0.023s
  ⏱️  LLM invoke: 45.234s

============================================================
PERFORMANCE SUMMARY
============================================================
LLM Calls: 1
Total Time: 45.659s
Pipeline: semantic → llm
============================================================

[COMPARISON MODE]
============================================================
📊 COMPARISON SUMMARY
============================================================
RAG Time: 45.659s
GraphRAG Time: 48.234s
Parallel Time: 48.234s (saved 45.659s)
Source Overlap: 2 documents
============================================================
```

---

## ⚡ GraphRAG Comparison Testing

### Khái niệm

**RAG (Retrieval-Augmented Generation)**:
- Tìm kiếm dựa trên semantic similarity
- Top-K documents gần nhất với query
- "Thầy bói xem voi" - chỉ thấy vài đoạn rời rạc

**GraphRAG (Graph-based RAG)**:
- Xây dựng knowledge graph từ documents
- 2-hop graph traversal để expand context
- "Nhìn thấy cả con voi" - hiểu relationships

### 📚 Tài liệu nên dùng

**🥇 Tốt nhất: Smart School Bus Tracking System.pdf**
- Size: 4.10 MB (lớn nhất)
- Nhiều components + relationships
- Architecture phức tạp
- Multi-topic với connections rõ ràng
- **Khuyến nghị: Dùng file này để test GraphRAG**

**🥈 Tốt: Bản sao của Chương 3.pdf**
- Size: 2.25 MB
- Nội dung học thuật có structure
- Có sections với cross-references

**🥉 Tạm được: antigravity&cloud_research.pdf**
- Size: 0.19 MB (nhỏ)
- Có 2 topics, có thể có connections
- Graph nhỏ → advantage không rõ

**❌ Không nên: CV files**
- Ít relationships
- Linear structure
- Single person info
- GraphRAG không có advantage

**Chi tiết:** Xem [`GRAPHRAG_DOCUMENT_GUIDE.md`](GRAPHRAG_DOCUMENT_GUIDE.md)

### Khi nào dùng GraphRAG?

✅ **GraphRAG tốt hơn khi:**
- Câu hỏi tổng quan, bao quát (summary, overview)
- Cần hiểu mối liên hệ giữa các entities
- Multi-hop reasoning (A → B → C)
- Tìm connections không rõ ràng

✅ **RAG tốt hơn khi:**
- Câu hỏi cụ thể, factoid
- Tìm thông tin chính xác trong 1-2 đoạn
- Cần speed (GraphRAG chậm hơn do graph traversal)
- Documents không có nhiều connections

### Cách test Comparison

#### Bước 1: Nhập câu hỏi
```
Query: "Tóm tắt toàn bộ nội dung chính trong tài liệu"
```

#### Bước 2: Click nút ⚡ Compare
- Nút ⚡ Compare nằm bên cạnh nút 📤 Gửi
- Click để chạy RAG + GraphRAG song song ngay lập tức
- Không cần chạy RAG trước rồi mới compare

#### Bước 3: Đợi parallel execution
```
⚖️ Đang so sánh RAG vs GraphRAG...
- RAG: Chạy semantic search + LLM
- GraphRAG: Chạy graph traversal + LLM
- Parallel: Cả 2 chạy đồng thời
```

#### Bước 4: Xem side-by-side comparison
```
┌─────────────────────────────┬─────────────────────────────┐
│ RAG                         │ GraphRAG                    │
├─────────────────────────────┼─────────────────────────────┤
│ [RAG Answer]                │ [GraphRAG Answer]           │
│                             │                             │
│ Sources: 3 docs             │ Sources: 5 docs             │
│ Time: 45.2s                 │ Time: 48.5s                 │
└─────────────────────────────┴─────────────────────────────┘

Stats: Overlap: 2 nguồn chung · RAG: 45.2s · GraphRAG: 48.5s
```

### Test Cases cho GraphRAG

#### TC5.1: Global Summary
**Document:** Smart School Bus Tracking System.pdf

**Query:**
```
Tóm tắt toàn bộ kiến trúc và chức năng của hệ thống Smart School Bus Tracking System
```

**Expected:**
- RAG: Tóm tắt 2-3 components (GPS, mobile app)
- GraphRAG: Tóm tắt toàn diện (hardware, software, network, database, security)
- GraphRAG sources > RAG sources (7 vs 3)
- Overlap < 50%

**Evaluation:**
- [ ] GraphRAG bao quát hơn
- [ ] GraphRAG có structure rõ ràng
- [ ] GraphRAG expand context tốt (3 seed → 7-10 docs)

---

#### TC5.2: Entity Relationships
**Document:** Smart School Bus Tracking System.pdf

**Query:**
```
Các thành phần hardware và software trong hệ thống Smart School Bus liên kết với nhau như thế nào?
```

**Expected:**
- RAG: Liệt kê các thành phần riêng lẻ
- GraphRAG: Giải thích connections (GPS → Server → Mobile App → Database)
- GraphRAG traverse graph để tìm links

**Evaluation:**
- [ ] GraphRAG hiểu relationships
- [ ] GraphRAG connect các entities
- [ ] Graph stats hiển thị (nodes, edges)

---

#### TC5.3: Multi-hop Question
**Document:** Smart School Bus Tracking System.pdf

**Query:**
```
GPS tracking thu thập dữ liệu và lưu trữ vào cloud storage như thế nào trong hệ thống?
```

**Expected:**
- RAG: Trả lời về GPS hoặc cloud riêng lẻ
- GraphRAG: Tìm connection GPS → Data Processing → Cloud Storage
- GraphRAG 2-hop traversal

**Evaluation:**
- [ ] GraphRAG tìm được connection
- [ ] GraphRAG multi-hop reasoning
- [ ] Expanded count > Seed count (2x-3x)

---

#### TC5.4: Performance Comparison
**Document:** Smart School Bus Tracking System.pdf

**Query:**
```
Tóm tắt toàn bộ hệ thống Smart School Bus
```

**Metrics to check:**

**Time:**
- RAG time: X.XXs
- GraphRAG time: Y.XXs
- Parallel time: max(X, Y) (not X+Y)
- Time saved: (X+Y) - max(X,Y)

**Sources:**
- RAG sources: N docs
- GraphRAG sources: M docs
- Overlap: K docs (common)
- Overlap rate: K/(N+M-K) %

**Graph Stats (GraphRAG only):**
- Seed count: Initial retrieved docs
- Expanded count: After 2-hop traversal
- Graph nodes: Total documents in graph
- Graph edges: Connections between docs

**Quality:**
- Completeness: GraphRAG > RAG for global questions
- Precision: RAG > GraphRAG for specific questions
- Coherence: Both should be coherent

**Evaluation:**
- [ ] Parallel execution works (time saved)
- [ ] Graph expansion works (expanded > seed)
- [ ] Quality appropriate for question type
- [ ] Stats displayed correctly

---

### GraphRAG Technical Details

#### Graph Construction
```
1. Tokenize documents → Extract terms
2. Build term-to-doc index
3. Create edges from term co-occurrence
4. Bonus edges for same file + nearby pages
5. Keep top 6 neighbors per node
```

#### 2-Hop Traversal
```
Seed nodes (from semantic search)
  ↓ score = 3.0
Hop 1 neighbors
  ↓ score = 2.0 + edge_weight * 0.25
Hop 2 neighbors
  ↓ score = 1.0 + edge_weight * 0.2
Rank by final score + query term overlap
```

#### Caching
- Graph index cached 1 hour (Streamlit cache)
- Reuse graph for multiple queries
- Rebuild only when documents change

---

### Troubleshooting GraphRAG

**Issue 1: GraphRAG quá chậm**
- Graph construction: ~2-5s (first time)
- Cached: <0.5s (subsequent queries)
- Solution: Graph được cache tự động

**Issue 2: GraphRAG không khác biệt**
- Check: Documents có connections không?
- Check: Query có phù hợp với GraphRAG không?
- Try: Global questions, summary, relationships

**Issue 3: Overlap quá cao (>80%)**
- Normal: Cả 2 methods tìm cùng docs
- GraphRAG expand thêm context
- Check expanded_count > seed_count

**Issue 4: Comparison button không hiện**
- Check: Đã có answer chưa?
- Check: vector_db có tồn tại không?
- Check: Không ở comparison mode rồi

---

### Best Practices

1. **Test với câu hỏi phù hợp:**
   - Global: "Tóm tắt...", "Tổng quan..."
   - Relationships: "Liên hệ...", "Ảnh hưởng..."
   - Multi-hop: "A ảnh hưởng đến B như thế nào?"

2. **So sánh metrics:**
   - Time: GraphRAG thường chậm hơn 10-20%
   - Sources: GraphRAG thường nhiều hơn 20-50%
   - Overlap: Thường 30-60%

3. **Đánh giá quality:**
   - Completeness: GraphRAG tốt hơn
   - Precision: RAG tốt hơn cho specific
   - Coherence: Cả 2 phải coherent

4. **Xem terminal logs:**
   - Graph stats: nodes, edges
   - Expansion: seed → expanded
   - Timing breakdown

---

## 📊 Current Status

### ✅ Ready for Testing
- [x] Test documents uploaded (5 PDFs)
- [x] FAISS indexes created (5 indexes)
- [x] Ollama running (qwen2.5:7b)
- [x] Performance logging enabled
- [x] Test documentation complete
- [x] Test scripts ready

### ⚠️ Dependencies
- [ ] Install Python packages: `pip install -r requirements.txt`

### 📝 Next Steps
1. Install dependencies
2. Run `python3 prepare_test_data.py` để verify
3. Chọn testing method (Quick/Automated/Full)
4. Execute tests
5. Document results

---

## 🎯 Expected Results

### Performance Targets
- **Model Load**: < 10s (first time only)
- **Query Embedding**: < 0.5s
- **Retrieval**: < 2s
- **LLM Generation**: < 60s (depends on hardware)
- **Total**: < 70s per query

### Quality Targets
- **Accuracy**: > 90% correct answers
- **Citation**: 100% with source tracking
- **Hallucination**: 0% (especially negative tests)
- **Confidence**: Appropriate scores (Self-RAG)

---

## 🐛 Known Issues & Solutions

### Issue 1: LLM quá chậm
**Symptom**: LLM invoke > 150s
**Solution**: 
- Use smaller model: `ollama pull qwen2.5:3b`
- Enable GPU if available

### Issue 2: Conversational không nhớ
**Symptom**: Không hiểu "nó", "cái đó"
**Solution**:
- Don't clear chat history
- Check query rewrite in logs

### Issue 3: Hybrid không khác biệt
**Symptom**: Kết quả giống semantic
**Solution**:
- Test với technical terms rõ ràng
- Check BM25 retriever hoạt động

---

## 📈 Testing Metrics

### Metrics được track:
1. **Accuracy** - Câu trả lời đúng không?
2. **Relevance** - Bám sát tài liệu không?
3. **Citation** - Source tracking đầy đủ không?
4. **Hallucination** - Có bịa không?
5. **Performance** - Thời gian chấp nhận được không?
6. **Confidence** - Score hợp lý không? (Self-RAG)
7. **Context** - Duy trì được không? (Conversational)

### Report Template:
```
Test Run: [Date]
Environment: [OS, Python, LLM, Hardware]

Results:
- Total: 16 tests
- Passed: X (Y%)
- Failed: Z

Feature Breakdown:
- Base RAG: X/4
- Self-RAG: X/4
- Hybrid: X/4
- Conversational: X/4

Issues: [List]
Recommendations: [List]
```

---

## 🎓 Best Practices

1. **Test incrementally** - Một feature một lúc
2. **Document everything** - Ghi chú chi tiết
3. **Compare modes** - Semantic vs Hybrid
4. **Track performance** - Xem terminal logs
5. **Test edge cases** - Không chỉ happy path
6. **Verify citations** - Check source accuracy
7. **Watch hallucination** - Đặc biệt negative tests
8. **Test conversation flow** - Nhiều turns

---

## 📞 Support & Resources

### Documentation
- `TESTING.md` - Full guide
- `TESTING_QUICK_GUIDE.md` - Quick reference
- `TESTING_README.md` - Overview
- `PERFORMANCE_LOGGING.md` - Performance analysis

### Scripts
- `prepare_test_data.py` - Environment check
- `run_tests.py` - Automated testing
- `test_performance_logging.py` - Performance test

### Checklist
- `test_checklist.md` - Track progress

---

## ✨ Summary

Bạn đã có:
- ✅ 20 test cases chi tiết cho 5 features
- ✅ 3 testing methods (Quick/Automated/Full)
- ✅ Performance logging đầy đủ
- ✅ Automated test scripts
- ✅ Complete documentation
- ✅ Test data ready (5 PDFs, 5 indexes)
- ✅ **GraphRAG comparison testing**

**Sẵn sàng để test! 🚀**

### Features Coverage:
1. ✅ Base RAG (4 tests) - Semantic search
2. ✅ Self-RAG (4 tests) - Advanced RAG
3. ✅ Hybrid Search (4 tests) - Keyword + Semantic
4. ✅ Conversational (4 tests) - Multi-turn chat
5. ✅ **RAG vs GraphRAG (4 tests) - Comparison** ⚡

---

## 🎬 Start Testing Now

```bash
# Quick check
python3 prepare_test_data.py

# Install dependencies if needed
pip install -r requirements.txt

# Start testing
streamlit run app.py

# Test GraphRAG comparison:
# 1. Ask a global question
# 2. Click "⚡ Compare with GraphRAG"
# 3. Compare side-by-side results

# Or run automated tests
python3 run_tests.py
```

**Good luck with testing! 🎯**

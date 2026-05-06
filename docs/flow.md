# Flow Hoạt Động Của SmartDoc AI

Tài liệu này mô tả chi tiết luồng hoạt động (flow) của từng tính năng chính trong hệ thống SmartDoc AI RAG. Tài liệu giúp hiểu rõ cách hệ thống hoạt động từ đầu đến cuối (end-to-end), sự luân chuyển dữ liệu qua các layer và các file cụ thể đảm nhiệm từng vai trò.

---

## 1. Tổng quan hệ thống

Flow chính của một hệ thống RAG (Retrieval-Augmented Generation) đi qua các bước cơ bản sau:

1. **Upload**: Người dùng tải tài liệu lên qua giao diện.
   - *File*: `app.py`, `src/presentation/components.py`
2. **Chunking**: Tài liệu được đọc và chia nhỏ thành các đoạn (chunks) vừa phải để xử lý.
   - *File*: `src/application/pipeline_doc.py`, `src/application/pipeline_pdf.py`
3. **Embedding**: Chuyển đổi các chunks văn bản thành vector (dãy số) có ý nghĩa ngữ nghĩa.
   - *File*: `src/data_layer/embeddings.py`
4. **Vector Store**: Lưu trữ các vector và metadata vào cơ sở dữ liệu vector.
   - *File*: `src/data_layer/vector_store.py`
5. **Retrieval**: Khi người dùng đặt câu hỏi, câu hỏi được chuyển thành vector và hệ thống tìm kiếm các chunks liên quan nhất trong Vector Store.
   - *File*: `src/application/rag_coordinator.py`, `src/application/rag_chain.py`
6. **LLM**: Các chunks văn bản tìm được kết hợp với câu hỏi tạo thành prompt gửi đến mô hình ngôn ngữ lớn (LLM).
   - *File*: `src/model_layer/llm_interface.py`
7. **Answer**: LLM sinh ra câu trả lời cuối cùng và hiển thị lại cho người dùng trên giao diện.
   - *File*: `app.py`

Kiến trúc hệ thống chia thành 4 layer chính:
- **Presentation Layer**: Giao diện người dùng (Streamlit).
- **Application Layer**: Xử lý logic nghiệp vụ, điều phối pipeline và quản lý chuỗi (chains).
- **Data Layer**: Quản lý cơ sở dữ liệu (Vector Store) và Embedding.
- **Model Layer**: Giao tiếp với LLM API (Google Gemini).

---

## 2. Core Features (Đã có)

### 🧩 Feature: PDF Upload & Processing

#### 🔄 Flow hoạt động
1. Người dùng upload file PDF thông qua giao diện ứng dụng Streamlit ở sidebar.
2. Ứng dụng đọc file, ghi tạm vào hệ thống file hoặc xử lý trực tiếp trên RAM.
3. Chuyển dữ liệu PDF thô cho pipeline chuyên biệt để đọc nội dung text bên trong PDF.

#### 📂 File liên quan
- `app.py` (Gọi component upload file)
- `src/presentation/components.py` (Render UI cho sidebar)
- `src/application/pipeline_pdf.py` (Xử lý chi tiết trích xuất text từ PDF)

#### 🧠 Giải thích ngắn
Cho phép người dùng đưa tài liệu của riêng họ vào hệ thống để AI có thể lấy làm ngữ cảnh trả lời câu hỏi. Đây là bước đầu vào bắt buộc của hệ thống.

---

### 🧩 Feature: Chunking Strategy

#### 🔄 Flow hoạt động
1. Nhận văn bản nguyên bản đã được trích xuất từ tài liệu.
2. Gọi các thư viện tách chữ (như `RecursiveCharacterTextSplitter`) từ application pipeline.
3. Chia đoạn với kích thước cố định (chunk_size) và đoạn gối lên nhau (chunk_overlap).
4. Trả về một list các đối tượng `Document` chứa nội dung đã được chunking kèm metadata cơ bản.

#### 📂 File liên quan
- `src/application/pipeline_doc.py` / `src/application/pipeline_pdf.py` (Chứa logic khởi tạo và chạy Text Splitter)

#### 🧠 Giải thích ngắn
LLM có giới hạn về độ dài ngữ cảnh đầu vào (context window) và vector embedding có hạn chế biểu diễn văn bản quá dài. Chunking đảm bảo độ chi tiết khi tìm kiếm và vừa vặn khi đưa vào LLM.

---

### 🧩 Feature: Embedding + FAISS Indexing

#### 🔄 Flow hoạt động
1. Sau khi chunking xong, ứng dụng gọi mô hình Embedding.
2. Từng text chunk được biến đổi thành một vector n-chiều.
3. Gọi tới kho lưu trữ FAISS (Vector Store).
4. Lưu danh sách các vector, kèm theo text tương ứng và các thông tin (metadata) vào local index.

#### 📂 File liên quan
- `src/data_layer/embeddings.py` (Cấu hình GoogleGenerativeAIEmbeddings)
- `src/data_layer/vector_store.py` (Cấu hình và điều khiển FAISS để lưu/tải vector)

#### 🧠 Giải thích ngắn
Giúp hệ thống "hiểu" ngữ nghĩa của văn bản. Việc index vector vào FAISS cho phép tìm kiếm cực nhanh (O(logN) hoặc tương đương) trong không gian nhiều chiều thay vì duyệt toàn văn bản.

---

### 🧩 Feature: RetrievalQA (base RAG)

#### 🔄 Flow hoạt động
1. User nhập câu hỏi ở input chat.
2. Application nhận câu hỏi, đi qua base chain (`rag_chain.py` / `chain_base.py`).
3. Chain gọi tới `vector_store` dưới vai trò một `retriever` để lấy top k chunks giống nhất với câu hỏi.
4. Chain chèn chunks vào prompt mẫu (`prompts.py`).
5. Gửi prompt cho `llm_interface`.
6. Trả lại đáp án cuối.

#### 📂 File liên quan
- `src/application/rag_coordinator.py` (Bộ điều phối chọn chain phù hợp)
- `src/application/rag_chain.py` (Chain RAG cơ bản)
- `src/application/prompts.py` (Quản lý template prompt)
- `src/model_layer/llm_interface.py` (Cấu hình ChatGoogleGenerativeAI)

#### 🧠 Giải thích ngắn
Tính năng cốt lõi nhất của app, mang lại khả năng trả lời chính xác dựa trên ngữ cảnh được cung cấp thay vì dựa vào kiến thức ảo giác của LLM.

---

### 🧩 Feature: Streamlit UI flow

#### 🔄 Flow hoạt động
1. Cài đặt các setting trang cơ bản (Title, Layout) từ file `app.py`.
2. Áp dụng các custom CSS và styling toàn cục.
3. Khởi tạo State (Session State) để lưu lịch sử và cờ (flags) hoạt động.
4. Render theo 2 vùng chính: Cột Sidebar (upload, config) và Cột Main (chat UI).
5. Cập nhật giao diện tự động mỗi khi state thay đổi.

#### 📂 File liên quan
- `app.py` (Điểm bắt đầu, quản lý layout tổng thể)
- `src/presentation/styles.py` (Chứa CSS / HTML động làm đẹp giao diện)
- `src/presentation/components.py` (Chứa các hàm vẽ UI tái sử dụng)

#### 🧠 Giải thích ngắn
Cung cấp giao diện trực quan cho người dùng tương tác mà không cần biết các câu lệnh dòng lệnh, mang lại trải nghiệm giống như ứng dụng Web.

---

## 3. Advanced Features

### 🧩 Feature: DOCX support

#### 🔄 Flow hoạt động
1. Tại sidebar, khi file có đuôi `.docx` được tải lên, ứng dụng chuyển hướng đến bộ xử lý Word.
2. Dùng thư viện python-docx (hoặc Docx2txtLoader) đọc cấu trúc file Word.
3. Gửi văn bản trích xuất được vào bước Chunking chung của hệ thống.

#### 📂 File liên quan
- `src/application/pipeline_doc.py` (Xử lý chi tiết đọc `.docx`)

#### 🧠 Giải thích ngắn
Mở rộng khả năng hỗ trợ định dạng phổ biến nhất của văn bản doanh nghiệp bên cạnh PDF.

---

### 🧩 Feature: Chat history

#### 🔄 Flow hoạt động
1. Người dùng bắt đầu trò chuyện.
2. Cứ mỗi cặp Câu hỏi / Trả lời được tạo ra, UI layer sẽ lưu vào mảng `st.session_state.messages`.
3. Khi load lại UI, toàn bộ mảng này được duyệt qua để vẽ lại đoạn hội thoại.
4. Khi chạy Conversational RAG, một phần của history này sẽ được gửi vào LLM dưới dạng context.

#### 📂 File liên quan
- `app.py` (Khởi tạo `st.session_state.messages`)
- `src/presentation/components.py` (Hàm hiển thị message list)

#### 🧠 Giải thích ngắn
Lưu vết để người dùng xem lại mạch trò chuyện, và cung cấp stateful context để bot hiểu được ngữ cảnh của các câu hỏi tiếp theo.

---

### 🧩 Feature: Clear data

#### 🔄 Flow hoạt động
1. Người dùng bấm nút "Clear Data" (Xóa dữ liệu / Đặt lại) trên Sidebar.
2. Gọi hàm callback hoặc logic reset.
3. Xóa các file vật lý (nếu có) trong thư mục tạm, xóa folder vector store (FAISS).
4. Reset `st.session_state` (messages rỗng, file đã nạp bị đánh dấu là False).
5. Reload trang Streamlit.

#### 📂 File liên quan
- `src/presentation/components.py` (Nút Clear / Sidebar)
- `app.py` (Reset state)
- `src/data_layer/vector_store.py` (Xóa index cục bộ)

#### 🧠 Giải thích ngắn
Giúp hệ thống giải phóng bộ nhớ và kho dữ liệu vector, tránh rác hoặc nhầm lẫn khi người dùng muốn đổi sang chủ đề / file tài liệu hoàn toàn mới.

---

### 🧩 Feature: Custom chunking

#### 🔄 Flow hoạt động
1. Người dùng điều chỉnh slider (Chunk Size, Chunk Overlap) trên giao diện cấu hình.
2. Thông số được cập nhật vào biến toàn cục hoặc gửi trực tiếp vào hàm process.
3. Lần tới khi có file được upload, module `pipeline_doc.py` sẽ sử dụng thông số size/overlap mới này để khởi tạo `RecursiveCharacterTextSplitter`.

#### 📂 File liên quan
- `src/presentation/components.py` (Sliders config)
- `src/application/pipeline_doc.py` (Text Splitter params)

#### 🧠 Giải thích ngắn
Cho phép người dùng nâng cao tuỳ biến chiến lược tách văn bản cho phù hợp với đặc thù cấu trúc từng loại tài liệu khác nhau.

---

### 🧩 Feature: Citation tracking

#### 🔄 Flow hoạt động
1. Khi Retriever lấy về top k chunks, hệ thống gom kèm metadata (Source, Page, v.v.).
2. Chain citation được kích hoạt, yêu cầu LLM khi trả lời phải "trích dẫn" cụ thể ID của chunks.
3. Backend phân tích kết quả trả về, đính kèm thông tin gốc (tên file, dòng / trang) vào cuối câu trả lời.
4. Presentation layer nhận dữ liệu mở rộng này và vẽ một khu vực "Nguồn trích dẫn" dưới message.

#### 📂 File liên quan
- `src/application/chain_citation.py` (Logic sinh câu trả lời có nguồn)
- `src/presentation/comp_citation.py` (UI hiển thị trích dẫn)

#### 🧠 Giải thích ngắn
Giảm ảo giác (hallucination), tăng độ tin cậy bằng cách chứng minh câu trả lời của AI đến từ phần nào trong tài liệu của người dùng.

---

### 🧩 Feature: Conversational RAG

#### 🔄 Flow hoạt động
1. Nhận câu hỏi mới nhất từ user + danh sách các câu hỏi / câu trả lời trước đó (History).
2. Gọi một LLM phụ (Condense Question Chain) để dịch câu hỏi mới + history thành một câu hỏi độc lập duy nhất (Standalone Question).
3. Dùng Standalone Question này để đi tìm kiếm vector (Retrieval).
4. Gửi kết quả chunk + Standalone Question cho LLM chính tạo đáp án.

#### 📂 File liên quan
- `src/application/chain_base.py` / `src/application/rag_chain.py` (Tùy chỉnh chain có memory)
- `app.py` (Truyền lịch sử vào chain)

#### 🧠 Giải thích ngắn
Giúp RAG hiểu được đại từ nhân xưng (nó, cái đó, anh ấy) khi người dùng hỏi các câu hỏi tiếp nối tự nhiên giống như đang trò chuyện.

---

### 🧩 Feature: Hybrid Search (BM25 + Vector)

#### 🔄 Flow hoạt động
1. Khi có tài liệu, tạo 2 bộ Index: 1 bộ FAISS (Vector) và 1 bộ BM25 (Từ khóa / Sparse).
2. Khi người dùng query, chạy song song 2 lệnh tìm kiếm ở 2 index.
3. Thu về list kết quả, sử dụng thuật toán Reciprocal Rank Fusion (RRF) hoặc ghép các kết quả (ensemble) để chọn ra những chunks tốt nhất chung.
4. Đưa chunks tốt nhất cho LLM.

#### 📂 File liên quan
- `src/application/chain_hybrid.py` (Logic Ensemble Retriever)
- `src/data_layer/vector_store.py` (Khởi tạo kết hợp FAISS + BM25)

#### 🧠 Giải thích ngắn
Khắc phục nhược điểm của Vector Search (kém khi tìm mã sản phẩm, từ khóa chính xác) bằng cách kết hợp với cách tìm kiếm từ khóa truyền thống (BM25).

---

### 🧩 Feature: Multi-document + Metadata filter

#### 🔄 Flow hoạt động
1. Người dùng up nhiều file cùng lúc.
2. Trong quá trình index, mỗi chunk được gán metadata mang nhãn `{"source": "tên-file.pdf"}`.
3. Khi query, nếu người dùng chọn (filter) cụ thể một file, tham số filter được gửi kèm lệnh FAISS `.similarity_search(query, filter={"source": "..."})`.
4. Chỉ các chunks thuộc file đó mới được lấy ra.

#### 📂 File liên quan
- `src/application/chain_multidoc.py` (Xử lý filter logic)
- `src/presentation/comp_multidoc.py` (UI chọn file để query)
- `src/data_layer/vector_store.py` (Nhận tham số filter)

#### 🧠 Giải thích ngắn
Rất cần thiết trong môi trường doanh nghiệp khi có một kho dữ liệu khổng lồ. Việc lọc Metadata thu hẹp phạm vi tìm kiếm, giúp tăng tốc độ và độ chính xác.

---

### 🧩 Feature: Re-ranking (Cross Encoder)

#### 🔄 Flow hoạt động
1. Retrieval ban đầu lấy ra số lượng chunk nhiều hơn bình thường (VD: top 15 thay vì top 4).
2. Các chunk này được gửi tới một model Cross-Encoder chuyên biệt (VD: BGE-Reranker hoặc Cohere).
3. Reranker chấm điểm (score) từng cặp `[Câu hỏi, Chunk]` về độ tương quan thực tế.
4. Sắp xếp lại (Sort) và cắt ra top K (VD: top 4) có điểm cao nhất để đưa vào LLM.

#### 📂 File liên quan
- `src/application/chain_rerank.py` (Contextual Compression Retriever)
- `src/application/rag_coordinator.py` (Điều hướng query qua Rerank)

#### 🧠 Giải thích ngắn
Mô hình embedding (Bi-encoder) tìm kiếm nhanh nhưng so sánh thô. Re-ranking (Cross-encoder) chậm hơn nhưng so sánh cực sâu, kết hợp 2 lớp giúp hệ thống vừa nhanh vừa siêu chuẩn.

---

### 🧩 Feature: Self-RAG

#### 🔄 Flow hoạt động
1. **Retrieve:** Lấy tài liệu theo câu hỏi.
2. **Grade/Critique (Tự đánh giá):** Dùng LLM nhỏ đánh giá xem document lấy về có thực sự chứa câu trả lời không. Nếu không, yêu cầu truy vấn lại (Rewrite query).
3. **Generate:** Sinh câu trả lời dựa trên document tốt.
4. **Hallucination Check:** Đánh giá lại câu trả lời sinh ra có bịa đặt so với document gốc hay không.

#### 📂 File liên quan
- `src/application/chain_selfrag.py` (Chứa các node đồ thị/luồng tự đánh giá: retrieve_node, grade_node, generate_node)

#### 🧠 Giải thích ngắn
Một kỹ thuật RAG nâng cao theo nguyên lý "Agentic". RAG tự có khả năng suy nghĩ, đánh giá chất lượng tài liệu lấy lên và kiểm duyệt câu trả lời của chính mình trước khi nhả ra cho người dùng.

---

## 🧠 Feature: GraphRAG

### ❓ GraphRAG là gì

**GraphRAG** là sự kết hợp giữa **Knowledge Graph (Đồ thị tri thức)** và RAG truyền thống.
Thay vì chỉ băm nhỏ văn bản thành các chunks rời rạc:
- Nó trích xuất ra các **Node** (Thực thể: Người, Công ty, Địa điểm...).
- Nó tìm ra các **Edge** (Quan hệ: Công ty A "thuộc sở hữu" Người B, Khái niệm X "là một phần của" Khái niệm Y).
Khi hệ thống có Knowledge Graph, các chunk thông tin được "liên kết" mạng lưới với nhau. Lúc này, AI không chỉ tìm "từ khóa giống nhau" mà còn có thể đi dọc theo các mối liên kết (Traverse graph) để nối chuỗi các thông tin đứt gãy.

### 🔄 Flow hoạt động (GraphRAG)

1. **Document -> chunk**: Văn bản thô được chia nhỏ.
2. **Extract entity / relation**: Dùng LLM quét qua các chunk để nhận diện danh từ chỉ thực thể (Entities) và các động từ nối (Relationships).
3. **Build graph (nodes + edges)**: Tổng hợp các thực thể và mối quan hệ thành mạng lưới đồ thị (Ví dụ sử dụng thư viện `networkx`).
4. **Lưu graph**: Dữ liệu đồ thị được lưu ở bộ nhớ (in-memory hoặc file `.graphml` / Neo4j / NebulaGraph).
5. **Query**:
   - Parse question: Phân tích câu hỏi của người dùng để tìm các Thực thể chính.
   - Map entity: Ánh xạ thực thể trong câu hỏi vào các Node trong Graph.
   - Traverse graph: Trích xuất các node lân cận và cạnh nối (sub-graph) có liên quan để lấy context.
6. **Kết hợp với vector search (hybrid reasoning)**: Nối chuỗi thông tin ngữ cảnh từ Đồ thị và Text từ Vector Database tạo thành một Context thống nhất, dồi dào gửi vào LLM.

### 🏗️ Cách implement vào project hiện tại

Đề xuất tạo mới một luồng (pipeline) song song với hệ thống RAG cơ bản hiện tại:

#### 📂 File mới nên tạo
- `src/application/graph_pipeline.py`: Chứa luồng xử lý chính khi người dùng upload file (Điều phối extract entity và build graph).
- `src/application/graph_builder.py`: Khai báo prompt và gọi LLM để trích xuất `(Entity_1) -[Relation]-> (Entity_2)` từ các text chunk.
- `src/application/graph_retriever.py`: Cung cấp hàm `.get_relevant_documents(query)` nhưng ở đây là lấy context từ graph (dạng diễn giải văn bản các mối quan hệ).
- `src/data_layer/graph_store.py`: Class quản lý cấu trúc lưu trữ đồ thị (sử dụng `networkx` cho nhẹ).

### 🔗 Integration với RAG hiện tại

GraphRAG không nên thay thế hoàn toàn Vector RAG, mà nên tích hợp theo dạng **Hybrid**:
- Khi có query, `rag_coordinator.py` kích hoạt lệnh chạy song song 2 luồng: `FAISS retrieval` và `GraphRAG retrieval`.
- Ngữ cảnh từ Vector FAISS cung cấp "độ sâu chi tiết" về nội dung đoạn văn.
- Ngữ cảnh từ GraphRAG cung cấp "góc nhìn rộng" về liên kết các thực thể.
- Hai luồng này được merge chung vào chuỗi Context trước khi đẩy qua cho Google Gemini sinh câu trả lời. Có thể cấu hình "GraphRAG mode" thành một công tắc (Toggle) trên Streamlit sidebar.

### ⚖️ So sánh

| Loại       | Ưu điểm       | Nhược điểm    |
| ---------- | ------------- | ------------- |
| **Vector RAG** | Nhanh, dễ triển khai, truy xuất các đoạn văn bản dài cực kỳ chính xác. | Thiếu sự kết nối, kém khi tài liệu phân mảnh thông tin, trả lời "Multi-hop" kém. |
| **GraphRAG**   | Khả năng suy luận (reasoning) đa bước xuất sắc, hiểu quan hệ toàn cục. | Xây dựng đồ thị tốn thời gian, tốn tiền gọi LLM trích xuất entity, cài đặt phức tạp. |

### 🧠 Use case
- **Multi-hop question (Hỏi đáp đa bước)**: VD: *"Giám đốc của công ty mua lại tập đoàn X năm ngoái là ai?"* -> Đòi hỏi phải tìm (1) Tập đoàn X bị ai mua -> (2) Công ty Y -> (3) Giám đốc công ty Y. Graph giải quyết bài toán này cực tốt.
- **Hỏi quan hệ / Tóm tắt toàn cục**: *"Mối quan hệ giữa nhân vật A và tổ chức B qua các thời kỳ là gì?"*
- **Sơ đồ tư duy**: Khi cần vẽ sơ đồ liên kết thay vì chỉ trả về text thuần tuý.

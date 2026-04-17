# SmartDoc AI

Ứng dụng hỏi đáp tài liệu PDF bằng RAG (Retrieval-Augmented Generation) với giao diện Streamlit.

## Mô tả dự án

- Upload file PDF.
- Tự động tách nội dung thành các đoạn nhỏ (chunks).
- Tạo vector embedding và lập chỉ mục bằng FAISS.
- Truy xuất ngữ cảnh liên quan và trả lời câu hỏi bằng mô hình LLM chạy local qua Ollama.

---

## 👥 Thành viên nhóm & Phân công

| Họ tên                 | MSSV        | Phụ trách                                                     |
| ---------------------- | ----------- | ------------------------------------------------------------- |
| Nguyễn Hoàng Anh       | 3123410007  | Lead · Setup dự án · Thiết kế hệ thống (Chương 3) · Câu 9, 10 |
| Đỗ Nhật Huy            | _(tự điền)_ | Câu 1, 2 · Tự test câu 1, 2 · UI (chung)                      |
| Hồ Hoàng Long          | 3123560046  | Câu 3, 4 · Tự test câu 3, 4 · Tổng hợp Chương 6 Testing       |
| Bùi Nguyễn Trọng Nghĩa | _(tự điền)_ | Câu 5, 6 · Tự test câu 5, 6 · UI (chung)                      |
| Lưu Phùng Khải Nguyên  | _(tự điền)_ | Câu 7, 8 · Tự test câu 7, 8 · UI (chung)                      |

### Chi tiết phân công

#### Nguyễn Hoàng Anh — Lead

- Setup dự án (môi trường, Makefile, app.py cơ bản)
- Thiết kế hệ thống (Chương 3): kiến trúc, Data Flow, các components
- Câu 9: Re-ranking với Cross-Encoder
- Câu 10: Advanced RAG với Self-RAG

```text
git checkout -b feature/cau-9-rerank
git checkout -b feature/cau-10-selfrag

src/application/chain_rerank.py      # Câu 9: re-ranking step
src/application/chain_selfrag.py     # Câu 10: Self-RAG logic
src/application/prompts.py           # Câu 10: self-eval prompt
src/model_layer/llm_interface.py     # Câu 10: Ollama inference tuning
```

#### Đỗ Nhật Huy

- Câu 1: Thêm hỗ trợ file DOCX
- Câu 2: Lưu trữ lịch sử hội thoại
- Tự viết test cho câu 1, 2

```text
git checkout -b feature/cau-1-docx
git checkout -b feature/cau-2-history

src/application/pipeline_docx.py     # Câu 1: DOCX loader
src/presentation/comp_upload.py      # Câu 1: UI upload DOCX
src/presentation/comp_history.py     # Câu 2: chat history UI
```

#### Hồ Hoàng Long

- Câu 3: Thêm nút xóa lịch sử
- Câu 4: Cải thiện chunk strategy
- Tự viết test cho câu 3, 4
- Tổng hợp test cases toàn nhóm → viết Chương 6 Testing

```text
git checkout -b feature/cau-3-clear
git checkout -b feature/cau-4-chunk

src/presentation/comp_clear.py       # Câu 3: clear button UI
src/application/pipeline_chunk.py   # Câu 4: chunk strategy config
```

#### Bùi Nguyễn Trọng Nghĩa

- Câu 5: Citation / source tracking
- Câu 6: Conversational RAG
- Tự viết test cho câu 5, 6

```text
git checkout -b feature/cau-5-citation
git checkout -b feature/cau-6-conversational

src/application/chain_citation.py        # Câu 5: source tracking trong chain
src/presentation/comp_citation.py        # Câu 5: hiển thị citation UI
src/application/chain_conversational.py  # Câu 6: ConversationalRetrievalChain
```

#### Lưu Phùng Khải Nguyên

- Câu 7: Hybrid search
- Câu 8: Multi-document RAG + metadata filtering
- Tự viết test cho câu 7, 8

```text
git checkout -b feature/cau-7-hybrid
git checkout -b feature/cau-8-multidoc

src/application/chain_hybrid.py      # Câu 7: BM25 + EnsembleRetriever
src/data_layer/vector_store.py       # Câu 7: tích hợp hybrid vào FAISS
src/application/chain_multidoc.py    # Câu 8: multi-doc + metadata filter
src/presentation/comp_multidoc.py    # Câu 8: UI chọn filter theo doc
```

---

## 🌿 Git Workflow

```bash
# Mỗi người tạo branch riêng theo tên tính năng
git checkout -b feature/cau-1-docx
git checkout -b feature/cau-2-history
git checkout -b feature/cau-3-clear
# ...

# Làm xong → push → tạo Pull Request → Lead review → merge vào dev
git push origin feature/cau-1-docx
```

> ⚠️ Không push thẳng lên `main`. Mọi thay đổi phải qua Pull Request vào nhánh `dev` trước.

---

## Kiến trúc tổng quan

Luồng xử lý chính trong ứng dụng:

1. Người dùng upload PDF trên giao diện Streamlit.
2. PDF được đọc bằng `PDFPlumberLoader`.
3. Văn bản được chia chunk bằng `RecursiveCharacterTextSplitter`.
4. Embedding được tạo bằng model `sentence-transformers`.
5. Chunks được index vào FAISS để truy xuất ngữ cảnh.
6. Câu hỏi người dùng được trả lời bởi chain `RetrievalQA` dùng mô hình `qwen2.5:7b` từ Ollama.

---

## Tiêu chí / yêu cầu

```text
1. Hệ thống RAG cốt lõi cần phải đáp ứng các yêu cầu cơ bản sau:
- Giao diện: Xây dựng giao diện web thân thiện (sử dụng Streamlit) cho phép người dùng tải lên tài liệu PDF

- Xử lý dữ liệu: Tích hợp công nghệ Text Embedding (sử dụng Multilingual MPNet) để chuyển đổi văn bản thành vector và dùng cơ sở dữ liệu FAISS để lưu trữ, tìm kiếm

- Mô hình ngôn ngữ: Tích hợp mô hình lớn Qwen2.5:7b chạy local thông qua framework Ollama

- Đa ngôn ngữ: Hỗ trợ xử lý xuất sắc tiếng Việt và hơn 50 ngôn ngữ khác, tự động phát hiện ngôn ngữ người dùng để trả lời cho phù hợp

- Môi trường: Ứng dụng phải chạy local (trên máy tính cá nhân), sử dụng hoàn toàn các mô hình open-source và miễn phí để đảm bảo tính riêng tư dữ liệu

2. 10 Tiêu chí / Yêu cầu phát triển dự án (Bắt buộc thực hiện)
Tài liệu liệt kê 10 yêu cầu phát triển với mức độ khó tăng dần để sinh viên mở rộng tính năng của hệ thống RAG cơ bản
:
- Hỗ trợ định dạng DOCX: Mở rộng khả năng xử lý file, cho phép tải lên và trích xuất văn bản từ file DOCX (dùng thư viện như python-docx hoặc DocxLoader)

- Lưu trữ lịch sử hội thoại: Hệ thống cần lưu các câu hỏi/trả lời trong session và hiển thị lịch sử chat ở thanh sidebar

- Xóa lịch sử và dữ liệu: Thêm các nút "Clear History" (xóa lịch sử chat) và "Clear Vector Store" (xóa tài liệu đã tải lên), kèm theo hộp thoại xác nhận trước khi xóa

- Cải thiện chiến lược Chunking: Thử nghiệm nhiều cấu hình cắt văn bản khác nhau (chunk_size: 500, 1000, 1500... và chunk_overlap: 50, 100, 200), so sánh độ chính xác và cho phép người dùng tự tùy chỉnh các tham số này

- Theo dõi nguồn trích dẫn (Citation/Source tracking): Hiển thị nguồn gốc thông tin (như số trang, vị trí trong PDF), highlight các đoạn văn được dùng để trả lời và cho phép người dùng click xem lại ngữ cảnh gốc

- Conversational RAG: Bổ sung bộ nhớ (memory) để hệ thống theo dõi ngữ cảnh cuộc hội thoại, giúp LLM trả lời được các câu hỏi nối tiếp (follow-up questions)

- Tìm kiếm lai (Hybrid Search): Kết hợp cả tìm kiếm ngữ nghĩa bằng vector (Semantic search) và tìm kiếm từ khóa (BM25 keyword search), triển khai ensemble retriever và so sánh hiệu suất với cách tìm kiếm thông thường

- Multi-document RAG và Lọc theo Metadata: Hỗ trợ tải lên nhiều file PDF cùng lúc, lưu trữ siêu dữ liệu (tên file, ngày upload, loại file), cho phép lọc khi tìm kiếm và chỉ rõ câu trả lời được lấy từ tài liệu nào

- Re-ranking với Cross-Encoder: Thêm bước đánh giá lại mức độ liên quan của kết quả tìm kiếm bằng mô hình cross-encoder, so sánh với phương pháp bi-encoder hiện tại và tối ưu hóa độ trễ

- Advanced RAG với Self-RAG: Triển khai cơ chế để LLM tự đánh giá câu trả lời, tự động viết lại câu hỏi (query rewriting), suy luận nhiều bước (multi-hop reasoning) và tính điểm độ tự tin (confidence scoring)

```

## Công nghệ sử dụng

- Python
- Streamlit
- LangChain
- FAISS (faiss-cpu)
- Sentence Transformers
- Ollama

---

## Cấu trúc thư mục

```text
GENERATIVE-AI/
│
├── app.py                                   # Entry point (streamlit run app.py)
├── requirements.txt                         # Danh sách thư viện
├── Makefile
├── .env                                     # Biến môi trường (nếu có)
├── README.md
│
├── data/                                    # Lớp Dữ liệu (Vật lý)
│   ├── pdfs/                                # PDF Document Storage
│   └── faiss_index/                         # FAISS Vector Store
│       └── .gitkeep
│
└── src/                                     # Mã nguồn chính
    ├── __init__.py
    │
    ├── presentation/                        # 1. Presentation Layer (Streamlit)
    │   ├── components.py                    # File chính — import các comp bên dưới
    │   ├── styles.py                        # Tuỳ chỉnh CSS cho Streamlit
    │   ├── comp_upload.py                   # Upload widget          → Huy (câu 1)
    │   ├── comp_history.py                  # Chat history UI        → Huy (câu 2)
    │   ├── comp_clear.py                    # Clear button UI        → Long (câu 3)
    │   ├── comp_citation.py                 # Citation display       → Nghĩa (câu 5)
    │   └── comp_multidoc.py                 # Multi-doc filter UI    → Nguyên (câu 8)
    │
    ├── application/                         # 2. Application Layer (LangChain)
    │   ├── pipeline.py                      # File chính — import các pipeline bên dưới
    │   ├── pipeline_pdf.py                  # PDF loader (base)
    │   ├── pipeline_docx.py                 # DOCX loader            → Huy (câu 1)
    │   ├── pipeline_chunk.py                # Chunk strategy         → Long (câu 4)
    │   ├── rag_chain.py                     # File chính — import các chain bên dưới
    │   ├── chain_base.py                    # Base RAG chain (base)
    │   ├── chain_citation.py                # Source tracking        → Nghĩa (câu 5)
    │   ├── chain_conversational.py          # Conversational RAG     → Nghĩa (câu 6)
    │   ├── chain_hybrid.py                  # Hybrid search          → Nguyên (câu 7)
    │   ├── chain_multidoc.py                # Multi-doc RAG          → Nguyên (câu 8)
    │   ├── chain_rerank.py                  # Re-ranking             → Anh (câu 9)
    │   ├── chain_selfrag.py                 # Self-RAG               → Anh (câu 10)
    │   └── prompts.py                       # Prompt Engineering
    │
    ├── data_layer/                          # 3. Data Layer
    │   ├── embeddings.py                    # Multilingual MPNet Embeddings
    │   └── vector_store.py                  # FAISS + BM25           → Nguyên (câu 7)
    │
    └── model_layer/                         # 4. Model Layer (Ollama)
        └── llm_interface.py                 # Qwen2.5:7b & Ollama Inference
```

---

## Yêu cầu môi trường

- Linux/macOS (hoặc môi trường có thể chạy Ollama)
- Python 3.10+

---

## Cài đặt nhanh (khuyến nghị)

### 1) Xem danh sách lệnh Makefile

```bash
make help
```

### 2) Cài đặt toàn bộ

```bash
make install
```

Lệnh trên sẽ:

- Tạo môi trường ảo `venv`.
- Cài dependencies từ `requirements.txt`.
- Cài Ollama (nếu chưa có).
- Pull model `qwen2.5:7b`.

### 3) Chạy ứng dụng

```bash
make run
```

Sau đó mở đường dẫn Streamlit hiển thị trong terminal (thường là http://localhost:8501).

---

## Cài đặt thủ công

```bash
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b
ollama serve
./venv/bin/streamlit run app.py
```

---

## Cách sử dụng

1. Mở ứng dụng Streamlit.
2. Upload một file PDF.
3. Chờ hệ thống xử lý tài liệu.
4. Nhập câu hỏi liên quan đến nội dung PDF.
5. Nhận câu trả lời ngắn gọn dựa trên ngữ cảnh truy xuất được.

---

## Lưu ý

- Ứng dụng đang cấu hình embedding chạy trên CPU.
- Trả lời phụ thuộc vào chất lượng OCR/nội dung trích xuất từ PDF.
- Nếu chưa chạy được model, kiểm tra:
  - `ollama serve` đã chạy chưa.
  - Model `qwen2.5:7b` đã pull thành công chưa.

---

## Dọn dẹp môi trường

```bash
make clean
```

---

## Checklist 10 yêu cầu phát triển (trạng thái hiện tại)

| #   | Yêu cầu                                          | Trạng thái | Ghi chú ngắn                                                                                   |
| --- | ------------------------------------------------ | ---------- | ---------------------------------------------------------------------------------------------- |
| 1   | Hỗ trợ DOCX                                      | Not Done   | Chưa có pipeline/loader DOCX và UI upload DOCX trong code hiện tại                             |
| 2   | Lưu trữ lịch sử hội thoại                        | Done       | Đã lưu/đọc/xóa từng cuộc hội thoại qua `data/history.py` + sidebar                             |
| 3   | Clear History + Clear Vector Store (có xác nhận) | Partial    | Đã có xóa từng đoạn chat; chưa có nút clear toàn bộ history và clear vector store đúng yêu cầu |
| 4   | Cải thiện chunk strategy (cho phép tùy chỉnh)    | Partial    | Đang chunk cố định; chưa có UI cho người dùng chỉnh `chunk_size`/`chunk_overlap`               |
| 5   | Citation / Source tracking                       | Done       | Đã trả lời kèm nguồn trang và hiển thị context theo nguồn                                      |
| 6   | Conversational RAG (memory trong chain)          | Partial    | Có lưu lịch sử chat, nhưng chain chưa dùng memory hội thoại để suy luận follow-up              |
| 7   | Hybrid Search (Semantic + BM25)                  | Partial    | Có file `chain_hybrid.py` nhưng chưa tích hợp luồng chạy chính trong app                       |
| 8   | Multi-document + metadata filtering              | Not Done   | Chưa có upload nhiều tài liệu + lọc theo metadata trong UI/chain                               |
| 9   | Re-ranking với Cross-Encoder                     | Not Done   | Chưa có module rerank hoạt động trong repo hiện tại                                            |
| 10  | Advanced RAG với Self-RAG                        | Not Done   | Chưa có module self-rag hoạt động trong repo hiện tại                                          |

### Tổng quan nhanh

- Done: 2/10 (yêu cầu 2, 5)
- Partial: 4/10 (yêu cầu 3, 4, 6, 7)
- Not Done: 4/10 (yêu cầu 1, 8, 9, 10)

## Đề xuất thứ tự triển khai nhanh nhất theo effort

1. Hoàn thiện yêu cầu 3 (Clear all history + clear vector store + hộp thoại xác nhận)
2. Hoàn thiện yêu cầu 4 (thêm thanh chỉnh `chunk_size`/`chunk_overlap` trên UI)
3. Hoàn thiện yêu cầu 6 (nối memory hội thoại vào chain để xử lý follow-up)
4. Hoàn thiện yêu cầu 7 (kết nối hybrid retriever vào luồng hỏi đáp chính)
5. Làm yêu cầu 1 (DOCX upload + loader + pipeline chung)
6. Làm yêu cầu 8 (multi-document + metadata filter)
7. Làm yêu cầu 9 (cross-encoder reranking)
8. Làm yêu cầu 10 (self-rag: self-eval, rewrite query, confidence score)

---

## License

Dự án được phát hành theo giấy phép MIT. Xem chi tiết trong file `LICENSE`.

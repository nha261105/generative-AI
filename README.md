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

## License

Dự án được phát hành theo giấy phép MIT. Xem chi tiết trong file `LICENSE`.

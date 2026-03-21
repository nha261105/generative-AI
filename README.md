# SmartDoc AI

Ứng dụng hỏi đáp tài liệu PDF bằng RAG (Retrieval-Augmented Generation) với giao diện Streamlit.

## Mô tả dự án

- Upload file PDF.
- Tự động tách nội dung thành các đoạn nhỏ (chunks).
- Tạo vector embedding và lập chỉ mục bằng FAISS.
- Truy xuất ngữ cảnh liên quan và trả lời câu hỏi bằng mô hình LLM chạy local qua Ollama.

---

## 👥 Thành viên nhóm & Phân công

| Họ tên | MSSV | Phụ trách |
|--------|------|-----------|
| Nguyễn Hoàng Anh | 3123410007 | · Setup dự án · Thiết kế hệ thống (Chương 3) · Câu 9, 10|
| Đỗ Nhật Huy | _(tự điền)_ | Câu 1, 2 · Tự test câu 1, 2 · UI (chung) |
| Hồ Hoàng Long | _(tự điền)_ | Câu 3, 4 · Tự test câu 3, 4 · Tổng hợp Chương 6 Testing |
| Bùi Nguyễn Trọng Nghĩa | _(tự điền)_ | Câu 5, 6 · Tự test câu 5, 6 · UI (chung) |
| Lưu Phùng Khải Nguyên | _(tự điền)_ | Câu 7, 8 · Tự test câu 7, 8 · UI (chung) |

### Chi tiết phân công

#### Nguyễn Hoàng Anh — Lead
- Setup dự án (môi trường, Makefile, app.py cơ bản)
- Thiết kế hệ thống (Chương 3): kiến trúc, Data Flow, các components
- Câu 9: Re-ranking với Cross-Encoder
- Câu 10: Advanced RAG với Self-RAG

#### Đỗ Nhật Huy
- Câu 1: Thêm hỗ trợ file DOCX
- Câu 2: Lưu trữ lịch sử hội thoại
- Tự viết test cho câu 1, 2

#### Hồ Hoàng Long
- Câu 3: Thêm nút xóa lịch sử
- Câu 4: Cải thiện chunk strategy
- Tự viết test cho câu 3, 4
- Tổng hợp test cases toàn nhóm → viết Chương 6 Testing

#### Bùi Nguyễn Trọng Nghĩa
- Câu 5: Citation / source tracking
- Câu 6: Conversational RAG
- Tự viết test cho câu 5, 6

#### Lưu Phùng Khải Nguyên
- Câu 7: Hybrid search
- Câu 8: Multi-document RAG + metadata filtering
- Tự viết test cho câu 7, 8

---

## 🌿 Git Workflow

```bash
# Mỗi người tạo branch riêng theo tên tính năng
git checkout -b feature/cau-1-docx
git checkout -b feature/cau-2-history
git checkout -b feature/cau-3-clear
# ...

# Làm xong → push → tạo Pull Request → merge(square) vào dev
git push origin feature/cau-1-docx
```

> Không push thẳng lên `main`.

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
smartdoc-ai/
│
├── app.py                  # Entry point — chỉ gọi UI
│
├── core/                   # Logic chính
│   ├── __init__.py
│   ├── loader.py           # Load PDF/DOCX         → Huy (câu 1)
│   ├── splitter.py         # Chunk text             → Long (câu 4)
│   ├── embedder.py         # Tạo embeddings
│   ├── vectorstore.py      # FAISS operations       → Nguyên (câu 7, 8)
│   ├── llm.py              # Ollama LLM
│   └── chain.py            # RAG chain              →Nghĩa (câu 6)
│
├── ui/                     # Streamlit UI components
│   ├── __init__.py
│   ├── sidebar.py          # Sidebar layout
│   └── main.py             # Main area layout
│
├── config.py               # Tất cả config tập trung 1 chỗ
│
├── docs/                   # Tài liệu hệ thống
│   ├── architecture.md     # Sơ đồ kiến trúc
│   └── system-design.md    # Chi tiết thiết kế
│
├── data/                   # Sample files
├── requirements.txt
├── Makefile
└── README.md
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
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import os
import time

from src.data_layer.vector_store import save_index

# Tắt tokenizer parallelism warning (xung đột với ThreadPoolExecutor)
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# Suppress unauthenticated HF Hub warning nếu token được set trong env
_hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
if _hf_token:
    os.environ.setdefault("HUGGINGFACE_HUB_TOKEN", _hf_token)


def _get_embeddings():
    """Dùng cached BatchEmbedder từ st.cache_resource nếu đang chạy trong Streamlit,
    fallback tạo mới nếu gọi từ script độc lập."""
    try:
        from src.model_layer.cache import get_cached_embedder
        return get_cached_embedder()
    except Exception:
        from src.data_layer.embeddings import BatchEmbedder
        return BatchEmbedder(batch_size=64)


# Alias public để app.py import khi cần load lại index
get_embeddings = _get_embeddings


def _load_pdf(pdf_path: str):
    """Load PDF, fallback PyPDFLoader → PDFPlumberLoader."""
    def _non_empty(docs):
        return [d for d in docs if (d.page_content or "").strip()]

    documents = _non_empty(PyPDFLoader(pdf_path).load())
    if not documents:
        documents = _non_empty(PDFPlumberLoader(pdf_path).load())
    return documents


def _chunk_documents(documents, chunk_size: int = 1000, chunk_overlap: int = 150):
    """Chia nhỏ văn bản, loại chunk rỗng."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    return [c for c in chunks if (c.page_content or "").strip()]


def _assign_metadata(chunks, pdf_path: str):
    """Gán filename, upload_time, file_type cho từng chunk."""
    detected_filename = Path(pdf_path).name
    upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_type = Path(pdf_path).suffix.lstrip(".").upper()

    for chunk in chunks:
        chunk.metadata["filename"] = detected_filename
        chunk.metadata["upload_time"] = upload_time
        chunk.metadata["file_type"] = file_type

    return chunks


# ──────────────────────────────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────────────────────────────

def process_pdf_to_vectorstore(
    pdf_path: str,
    vector_store_path: str,
    chunk_size: int = 500,  # Optimized: 1000 → 500
    chunk_overlap: int = 100,  # Optimized: 150 → 100
    return_stats: bool = False,
):
    """Quy trình single-file: Load PDF -> Chunk -> Metadata -> Embedding -> FAISS"""
    total_start = time.perf_counter()

    # 1. Load
    load_start = time.perf_counter()
    documents = _load_pdf(pdf_path)
    if not documents:
        raise ValueError(
            "Không trích xuất được văn bản từ PDF. "
            "File có thể là ảnh scan/OCR chưa nhận dạng."
        )
    load_time = time.perf_counter() - load_start

    # 2. Chunk
    chunk_start = time.perf_counter()
    chunks = _chunk_documents(documents, chunk_size, chunk_overlap)
    if not chunks:
        raise ValueError(
            "Không tạo được chunk văn bản hợp lệ từ PDF. "
            "Vui lòng thử file khác hoặc OCR trước khi upload."
        )
    chunk_time = time.perf_counter() - chunk_start

    # 3. Metadata
    chunks = _assign_metadata(chunks, pdf_path)

    # 4. Embedding + FAISS
    embed_start = time.perf_counter()
    embeddings = _get_embeddings()
    vector_db = FAISS.from_documents(chunks, embeddings)
    save_index(vector_db, vector_store_path)
    embed_and_save_time = time.perf_counter() - embed_start

    total_time = time.perf_counter() - total_start

    stats = {
        "doc_count": len(documents),
        "chunk_count": len(chunks),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "load_time_sec": round(load_time, 3),
        "chunk_time_sec": round(chunk_time, 3),
        "embed_and_save_time_sec": round(embed_and_save_time, 3),
        "total_time_sec": round(total_time, 3),
    }

    if return_stats:
        return vector_db, stats
    return vector_db


def _process_single_file(
    file_path: str,
    chunk_size: int,
    chunk_overlap: int,
) -> tuple[list, list[str]]:
    """
    Load + chunk một file, trả về (chunks, errors).
    Hàm này chạy trong thread riêng — không gọi embedding ở đây
    vì embedding model không thread-safe khi dùng CPU.
    """
    path_obj = Path(file_path)
    ext = path_obj.suffix.lower()
    errors: list[str] = []

    try:
        if ext == ".pdf":
            documents = _load_pdf(file_path)
            if not documents:
                return [], [f"{path_obj.name}: không trích xuất được văn bản PDF"]
            chunks = _chunk_documents(documents, chunk_size, chunk_overlap)
            chunks = _assign_metadata(chunks, file_path)
            return chunks, []

        elif ext == ".docx":
            from src.application.pipeline_doc import _read_docx, _is_valid_chunk
            documents = _read_docx(file_path, path_obj.name)
            if not documents:
                return [], [f"{path_obj.name}: không trích xuất được văn bản DOCX"]
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            chunks = splitter.split_documents(documents)
            chunks = [c for c in chunks if _is_valid_chunk(c.page_content)]
            chunks = _assign_metadata(chunks, file_path)
            return chunks, []

        else:
            return [], [f"{path_obj.name}: định dạng không hỗ trợ ({ext})"]

    except Exception as exc:
        return [], [f"{path_obj.name}: {exc}"]


def process_multiple_files_to_vectorstore(
    file_paths: list[str],
    vector_store_path: str,
    chunk_size: int = 500,  # Optimized: 1000 → 500
    chunk_overlap: int = 100,  # Optimized: 150 → 100
):
    """
    Multi-file: Load + Chunk song song (ThreadPoolExecutor) → Embed batch → FAISS.

    Benchmark estimate so với tuần tự:
      - 3 files PDF ~50 trang mỗi file:
        Tuần tự:  ~180-220s (load+chunk+embed)
        Song song: ~90-120s  → tiết kiệm ~40-50% ở bước load/chunk
      - Embedding vẫn single-threaded (model không thread-safe) nhưng
        dùng BatchEmbedder batch_size=64 → tiết kiệm thêm ~30% so với default.
    """
    total_start = time.perf_counter()
    all_chunks = []
    total_docs = 0
    errors: list[str] = []

    # Bước 1: Load + chunk song song — I/O bound nên ThreadPoolExecutor phù hợp
    # max_workers=4 đủ cho hầu hết máy, tránh quá nhiều thread tranh nhau disk I/O
    max_workers = min(4, len(file_paths))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(_process_single_file, fp, chunk_size, chunk_overlap): fp
            for fp in file_paths
        }
        for future in as_completed(future_to_path):
            chunks, file_errors = future.result()
            errors.extend(file_errors)
            if chunks:
                total_docs += 1
                all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError(
            "Không tạo được chunk từ bất kỳ file nào. "
            + (" | ".join(errors) if errors else "")
        )

    # Bước 2: Embed toàn bộ chunks một lần (BatchEmbedder)
    embeddings = _get_embeddings()
    vector_db = FAISS.from_documents(all_chunks, embeddings)
    save_index(vector_db, vector_store_path)

    total_time = time.perf_counter() - total_start
    stats = {
        "file_count": len(file_paths),
        "doc_count": total_docs,
        "chunk_count": len(all_chunks),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "total_time_sec": round(total_time, 3),
        "errors": errors,
    }
    return vector_db, stats


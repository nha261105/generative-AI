from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from datetime import datetime
from pathlib import Path
import time


def _get_embeddings():
    """Shared embeddings factory (MPNet 768-dim, đa ngôn ngữ)."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


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
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
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
    vector_db.save_local(vector_store_path)
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


def process_multiple_files_to_vectorstore(
    file_paths: list[str],
    vector_store_path: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
):
    """Multi-file: Load N PDFs/DOCXs -> Chunk -> Metadata per file -> One FAISS index."""
    total_start = time.perf_counter()
    all_chunks = []
    total_docs = 0
    errors = []

    for file_path in file_paths:
        try:
            path_obj = Path(file_path)
            ext = path_obj.suffix.lower()
            if ext == ".pdf":
                documents = _load_pdf(file_path)
                if not documents:
                    errors.append(f"{path_obj.name}: không trích xuất được văn bản PDF")
                    continue
                total_docs += len(documents)
                chunks = _chunk_documents(documents, chunk_size, chunk_overlap)
                chunks = _assign_metadata(chunks, file_path)
                all_chunks.extend(chunks)
            elif ext == ".docx":
                from src.application.pipeline_doc import _read_docx, _is_valid_chunk
                from langchain_text_splitters import RecursiveCharacterTextSplitter
                documents = _read_docx(file_path, path_obj.name)
                if not documents:
                    errors.append(f"{path_obj.name}: không trích xuất được văn bản DOCX")
                    continue
                total_docs += len(documents)
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=["\n\n", "\n", ". ", " ", ""],
                )
                chunks = splitter.split_documents(documents)
                chunks = [c for c in chunks if _is_valid_chunk(c.page_content)]
                chunks = _assign_metadata(chunks, file_path)
                all_chunks.extend(chunks)
            else:
                errors.append(f"{path_obj.name}: định dạng không hỗ trợ ({ext})")
        except Exception as exc:
            errors.append(f"{Path(file_path).name}: {exc}")

    if not all_chunks:
        raise ValueError(
            "Không tạo được chunk từ bất kỳ file nào. "
            + (" | ".join(errors) if errors else "")
        )

    embeddings = _get_embeddings()
    vector_db = FAISS.from_documents(all_chunks, embeddings)
    vector_db.save_local(vector_store_path)

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


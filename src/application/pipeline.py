from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import time

def process_pdf_to_vectorstore(
    pdf_path: str,
    vector_store_path: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    return_stats: bool = False,
):
    """Quy trình: Load PDF -> Chunking -> Embedding -> Save FAISS"""

    def _non_empty_docs(docs):
        return [doc for doc in docs if (doc.page_content or "").strip()]

    total_start = time.perf_counter()

    # 1. Load tài liệu
    # Ưu tiên PyPDFLoader, fallback sang PDFPlumberLoader nếu text rỗng.
    load_start = time.perf_counter()
    documents = PyPDFLoader(pdf_path).load()
    documents = _non_empty_docs(documents)

    if not documents:
        documents = PDFPlumberLoader(pdf_path).load()
        documents = _non_empty_docs(documents)

    if not documents:
        raise ValueError(
            "Không trích xuất được văn bản từ PDF. "
            "File có thể là ảnh scan/OCR chưa nhận dạng."
        )
    load_time = time.perf_counter() - load_start
    
    # 2. Chia nhỏ văn bản (Chunking)
    # Giữ nguyên cấu trúc câu để không mất ngữ cảnh
    chunk_start = time.perf_counter()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)

    # Loại bỏ các chunk rỗng để tránh tạo embedding rỗng trong FAISS.
    chunks = [chunk for chunk in chunks if (chunk.page_content or "").strip()]
    if not chunks:
        raise ValueError(
            "Không tạo được chunk văn bản hợp lệ từ PDF. "
            "Vui lòng thử file khác hoặc OCR trước khi upload."
        )
    chunk_time = time.perf_counter() - chunk_start
    
    # 3. Khởi tạo Embeddings (MPNet 768-dim như thiết kế)
    # Model này hỗ trợ đa ngôn ngữ cực tốt
    embed_start = time.perf_counter()
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # 4. Tạo Vector Store và lưu cục bộ
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

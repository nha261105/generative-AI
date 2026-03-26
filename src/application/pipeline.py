import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

def process_pdf_to_vectorstore(pdf_path: str, vector_store_path: str):
    """Quy trình: Load PDF -> Chunking -> Embedding -> Save FAISS"""
    
    # 1. Load tài liệu
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    # 2. Chia nhỏ văn bản (Chunking)
    # Giữ nguyên cấu trúc câu để không mất ngữ cảnh
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    
    # 3. Khởi tạo Embeddings (MPNet 768-dim như thiết kế)
    # Model này hỗ trợ đa ngôn ngữ cực tốt
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # 4. Tạo Vector Store và lưu cục bộ
    vector_db = FAISS.from_documents(chunks, embeddings)
    vector_db.save_local(vector_store_path)
    
    return vector_db
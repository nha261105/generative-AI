from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents import Document

def load_and_split_pdf(
        file_path: str,
        chunks_size: 100,
        chunks_overlap: 100,
) -> List[Document]:
    loader = PDFPlumberLoader(file_path)
    docs = loader.load()

    spliter = RecursiveCharacterTextSplitter(
        chunks_size = chunks_size,
        chunks_overlap = chunks_overlap
    )

    chunks = spliter.split_documents(docs)

    return chunks
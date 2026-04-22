# NOTE: Standalone PDF utility — NOT used by the main app pipeline.
# The main pipeline used by app.py is pipeline.py.

from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents import Document


def load_and_split_pdf(
        file_path: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
) -> List[Document]:
    loader = PDFPlumberLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = splitter.split_documents(docs)

    return chunks
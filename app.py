import streamlit as st
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import tempfile
import os

st.title("SmartDoc AI 📄")
st.caption("Upload PDF và đặt câu hỏi")

# Upload file
uploaded_file = st.file_uploader("Chọn file PDF", type=["pdf"])

if uploaded_file:
    # Lưu file tạm
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    with st.spinner("Đang xử lý tài liệu..."):
        # Load
        loader = PDFPlumberLoader(tmp_path)
        docs = loader.load()

        # Split
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        chunks = splitter.split_documents(docs)
        st.success(f"Đã chia thành {len(chunks)} chunks")

        # Embed
        embedder = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )

        # Vector store
        vector_store = FAISS.from_documents(chunks, embedder)
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        st.success("Tài liệu đã sẵn sàng!")

    # LLM
    llm = Ollama(model="qwen2.5:7b")

    # Prompt
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""Dùng ngữ cảnh sau để trả lời câu hỏi.
Nếu không biết, hãy nói không biết. Trả lời ngắn gọn 3-4 câu.

Ngữ cảnh: {context}
Câu hỏi: {question}
Trả lời:"""
    )

    # Chain
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt}
    )

    # Input câu hỏi
    question = st.text_input("Đặt câu hỏi về tài liệu:")
    if question:
        with st.spinner("Đang trả lời..."):
            answer = chain.run(question)
            st.markdown("**Trả lời:**")
            st.write(answer)

    os.unlink(tmp_path)

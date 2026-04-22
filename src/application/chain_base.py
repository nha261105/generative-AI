# NOTE: Basic RAG chain without citation — NOT used by the main app.
# The main app uses chain_citation.py and other chain_* modules.

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate


def get_prompt(language: str = "vi") -> PromptTemplate:
    """Trả về prompt template theo ngôn ngữ."""

    if language == "vi":
        template = """Dùng ngữ cảnh để trả lời câu hỏi.
Nếu không biết, hãy nói không biết. Trả lời ngắn gọn 3-4 câu bằng tiếng Việt.

Ngữ cảnh: {context}
Câu hỏi: {question}
Trả lời:"""
    else:
        template = """Use the following context to answer the question.
If you don't know, just say you don't know. Keep answer concise (3-4 sentences).

Context: {context}
Question: {question}
Answer:"""

    return PromptTemplate(
        input_variables=["context", "question"],
        template=template,
    )


def create_rag_chain(retriever, llm, language: str = "vi"):
    prompt = get_prompt(language)
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )
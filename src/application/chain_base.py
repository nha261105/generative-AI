from langchain.chains import retrieval_qa
from langchain.prompts import PromptTemplate

def get_promt(language: str = "vi") -> PromptTemplate:
    """Trả về promt template theo ngôn ngữ."""

    if language == "vi":
        template = """Dùng ngữ cảnh để trả lời câu hỏi.
Nếu không biết, hãy nói không biết.Trả lời ngắn gọn 3-4 câu bằng tiếng Việt.

Ngữ cảnh: {context}
Câu hỏi: {question}
Trả lời:"""
    else:
        template = """Use the following context to answer the question.
If you don't know, just say you don't know. Keep answer concise(3-4 sentenses).

Context: {context}
Question: {question}
Answer:"""

    return PromptTemplate(
        input_types=["context", "question"],
        template=template
    )

def create_rag_chain(retriever, llm, language: str = "vi") -> retrieval_qa:
    promt = get_promt(language)
    return retrieval_qa.from_chain_type(
        llm = llm,
        retriever = retriever,
        return_source_documents = True,
        chain_type_kwargs={"promt":promt}
    )
    
        
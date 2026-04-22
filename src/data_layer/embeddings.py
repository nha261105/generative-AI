# NOTE: Standalone embedding factory — NOT used by the main app.
# The main pipeline (pipeline.py) creates embeddings inline.

from langchain_community.embeddings import HuggingFaceEmbeddings


def get_embedder(
        model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        device: str = "cpu",
):
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )
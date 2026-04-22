# NOTE: Standalone LLM factory — NOT used by the main app.
# Individual chain modules (chain_citation.py, etc.) instantiate Ollama directly.

from langchain_community.llms import Ollama


def get_llm(
        model: str = "qwen2.5:7b",
        temperature: float = 0.7,
        top_p: float = 0.9,
        repeat_penalty: float = 1.1,
):
    return Ollama(
        model=model,
        temperature=temperature,
        top_p=top_p,
        repeat_penalty=repeat_penalty,
    )

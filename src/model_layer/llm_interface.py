from langchain_community.llms import ollama

def get_llm(
        model: str = "qwen2.5:7b",
        temperature: float = 0.7,
        top_p: float = 0.9,
        repeat_penalty: float = 1.1
):
    return ollama(
        model = model,
        temperature = temperature,
        top_p = top_p,
        repeat_penalty = repeat_penalty
    )


"""
src/model_layer/cache.py
─────────────────────────
Singleton cache cho các heavy objects dùng st.cache_resource.

Tất cả chain/pipeline import từ đây thay vì khởi tạo inline,
đảm bảo mỗi object chỉ load 1 lần trong suốt vòng đời Streamlit app.

Objects được cache:
  - BatchEmbedder   (~400 MB, load ~5-10s)
  - Ollama LLM      (connection object, ~200-500ms)
  - CrossEncoder    (~100 MB, load ~2-3s)
  - LLM Responses   (cache 10 phút cho repeated queries)
"""

import streamlit as st
import hashlib


@st.cache_resource(show_spinner=False)
def get_cached_embedder():
    """Load embedding model một lần duy nhất, dùng BatchEmbedder tối ưu."""
    import time
    t0 = time.perf_counter()
    print(f"  📦 Loading embedding model...")
    
    from src.data_layer.embeddings import BatchEmbedder
    embedder = BatchEmbedder(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        batch_size=64,
        device="cpu",
        normalize=True,
    )
    
    load_time = time.perf_counter() - t0
    print(f"  ⏱️  Embedding model loaded: {load_time:.3f}s")
    return embedder


@st.cache_resource(show_spinner=False)
def get_cached_llm(temperature: float = 0.7):
    """
    Cache Ollama instance theo temperature.
    temperature=0.7 → answer
    temperature=0.1 → conv rewrite
    temperature=0.3 → self-rag eval
    """
    import time
    t0 = time.perf_counter()
    print(f"  📦 Loading LLM (temp={temperature})...")
    
    from langchain_community.llms import Ollama
    llm = Ollama(
        model="qwen2.5:7b",
        temperature=temperature,
        top_p=0.9,
        repeat_penalty=1.1,
    )
    
    load_time = time.perf_counter() - t0
    if load_time > 0.1:
        print(f"  ⏱️  LLM loaded: {load_time:.3f}s")
    return llm


@st.cache_resource(show_spinner=False)
def get_cached_reranker():
    """Cache CrossEncoder reranker một lần duy nhất."""
    from sentence_transformers import CrossEncoder
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


@st.cache_data(ttl=600, show_spinner=False)
def get_cached_llm_response(prompt: str, temperature: float = 0.7) -> str:
    """
    Cache LLM responses for 10 minutes to speed up repeated queries.
    
    Args:
        prompt: Full prompt string
        temperature: LLM temperature (used for cache key)
    
    Returns:
        LLM response string
    
    Note: Cache key includes prompt hash + temperature to avoid collisions.
    """
    # Log LLM call
    try:
        from src.utils.logger import get_logger
        get_logger().log_llm_call(f"temp={temperature}")
    except:
        pass  # Fail silently if logger not available
    
    llm = get_cached_llm(temperature=temperature)
    return str(llm.invoke(prompt))


def get_llm_response_with_cache(prompt: str, temperature: float = 0.7, use_cache: bool = True) -> str:
    """
    Get LLM response with optional caching.
    
    Args:
        prompt: Full prompt string
        temperature: LLM temperature
        use_cache: If True, use cached response (default). If False, bypass cache.
    
    Returns:
        LLM response string
    """
    if use_cache:
        return get_cached_llm_response(prompt, temperature)
    else:
        llm = get_cached_llm(temperature=temperature)
        return str(llm.invoke(prompt))

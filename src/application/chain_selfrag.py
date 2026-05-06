import json
import re
from typing import Dict, List, Tuple
import time

from src.application.chain_base import BaseRAGChain
from src.application.prompts import (
    get_self_rag_eval_prompt,
    get_self_rag_rewrite_prompt,
    get_self_rag_eval_and_rewrite_prompt,  # NEW: Phase 2 optimization
)
from src.model_layer.cache import get_cached_llm


class SelfRAGChain(BaseRAGChain):
    """
    Self-RAG chain với multi-hop reasoning và confidence scoring.
    
    Dùng LLM temperature thấp (0.3) cho eval/rewrite.
    """
    
    def __init__(self):
        super().__init__(temperature=0.3)
    
    @staticmethod
    def _extract_json_payload(text: str) -> dict:
        """
        Parse JSON từ LLM output với 3 lớp fallback:
          1. Parse trực tiếp toàn bộ text
          2. Tìm block {...} đầu tiên và parse
          3. Extract từng field bằng regex
        """
        if not text:
            return {}
        
        raw = text.strip()
        
        # Lớp 1: parse trực tiếp
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        
        # Lớp 2: tìm JSON block đầu tiên
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            snippet = raw[start: end + 1]
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                pass
        
        # Lớp 3: regex fallback
        result: dict = {}
        
        conf_match = re.search(r'"?confidence"?\s*:\s*([0-9.]+)', raw)
        if conf_match:
            try:
                result["confidence"] = float(conf_match.group(1))
            except ValueError:
                pass
        
        rewrite_match = re.search(r'"?needs_rewrite"?\s*:\s*(true|false)', raw, re.IGNORECASE)
        if rewrite_match:
            result["needs_rewrite"] = rewrite_match.group(1).lower() == "true"
        
        query_match = re.search(r'"?rewritten_query"?\s*:\s*"([^"]*)"', raw)
        if query_match:
            result["rewritten_query"] = query_match.group(1)
        
        return result
    
    def _retrieve_docs(self, vector_db, query: str, k: int = 5):
        """Retrieve documents từ vector store."""
        retriever = vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k, "fetch_k": 20},
        )
        return retriever.invoke(query)
    
    def get_answer(
        self,
        query: str,
        vector_db,
        chat_history: List[Dict] | None = None,
        confidence_threshold: float = 0.62,
        early_stop_threshold: float = 0.85,
        initial_k: int = 5,
        use_combined_prompt: bool = True,  # NEW: Phase 2 - use combined eval+rewrite
    ) -> Tuple[str, List[Dict], Dict]:
        start_ts = time.perf_counter()
        llm_calls = 0  # NEW: Track LLM calls
        
        # Hop 1: Initial retrieval
        docs = self._retrieve_docs(vector_db, query, k=initial_k)
        if not docs:
            response, sources = self.get_empty_response()
            return response, sources, {
                "hops_used": 1,
                "confidence": 0.0,
                "rewritten_query": "",
                "total_time_sec": round(time.perf_counter() - start_ts, 3),
                "early_stopped": False,
                "llm_calls": llm_calls,
            }
        
        context_string, sources = self.build_context_and_sources(docs)
        answer = self.generate_answer(query, context_string, chat_history)
        llm_calls += 1  # Answer generation
        
        # Early stopping: Skip eval for simple/clear queries
        UNCERTAINTY_WORDS = ["có thể", "không chắc", "không rõ", "maybe", "perhaps", "unclear"]
        is_simple_query = (
            len(query.split()) <= 15 and  # OPTIMIZED: 10→15 words
            not any(word in answer.lower() for word in UNCERTAINTY_WORDS) and
            len(docs) >= 3  # Đủ context
        )
        
        if is_simple_query:
            benchmark = {
                "hops_used": 1,
                "confidence": early_stop_threshold,
                "rewritten_query": "",
                "total_time_sec": round(time.perf_counter() - start_ts, 3),
                "early_stopped": True,
                "eval_skipped": True,
                "llm_calls": llm_calls,
            }
            return answer, sources, benchmark
        
        # Phase 2 Optimization: Use combined eval+rewrite prompt
        if use_combined_prompt:
            # Single LLM call for both eval and rewrite
            combined_prompt = get_self_rag_eval_and_rewrite_prompt().format(
                question=query,
                chat_history=self.format_chat_history(chat_history),
                context=context_string,
                answer=answer,
            )
            eval_raw = self.llm.invoke(combined_prompt)
            llm_calls += 1  # Combined eval+rewrite
            eval_payload = self._extract_json_payload(eval_raw)
        else:
            # Original: Separate eval call
            eval_prompt = get_self_rag_eval_prompt().format(
                question=query,
                context=context_string,
                answer=answer,
            )
            eval_raw = self.llm.invoke(eval_prompt)
            llm_calls += 1  # Eval only
            eval_payload = self._extract_json_payload(eval_raw)
        
        confidence = max(0.0, min(1.0, float(eval_payload.get("confidence", 0.5))))
        needs_rewrite = bool(eval_payload.get("needs_rewrite", False))
        rewritten_query = str(eval_payload.get("rewritten_query", "")).strip()
        
        hops_used = 1
        early_stopped = False
        
        # Early stopping: If confidence very high, skip hop 2
        if confidence >= early_stop_threshold:
            early_stopped = True
            benchmark = {
                "hops_used": 1,
                "confidence": round(confidence, 3),
                "rewritten_query": "",
                "total_time_sec": round(time.perf_counter() - start_ts, 3),
                "early_stopped": True,
                "eval_skipped": False,
                "llm_calls": llm_calls,
            }
            return answer, sources, benchmark
        
        # Hop 2: Rewrite and retry if needed
        if needs_rewrite or confidence < confidence_threshold:
            hops_used = 2
            
            # If combined prompt didn't provide rewritten_query, call rewrite separately
            if not rewritten_query and not use_combined_prompt:
                rewrite_prompt = get_self_rag_rewrite_prompt().format(
                    question=query,
                    chat_history=self.format_chat_history(chat_history),
                )
                rewritten_query = str(self.llm.invoke(rewrite_prompt)).strip()
                llm_calls += 1  # Separate rewrite call
            
            if rewritten_query:
                docs_retry = self._retrieve_docs(vector_db, rewritten_query, k=initial_k)
                if docs_retry:
                    context_hop2, sources_hop2 = self.build_context_and_sources(docs_retry)
                    answer_hop2 = self.generate_answer(rewritten_query, context_hop2, chat_history)
                    llm_calls += 1  # Hop 2 answer
                    
                    # Synthesis
                    synthesis_prompt = f"""
Bạn là SmartDoc AI. Hãy tổng hợp kết quả từ 2 hop truy xuất để trả lời câu hỏi gốc.

YÊU CẦU:
1. Trả lời dựa trên bằng chứng trong 2 context bên dưới.
2. Mỗi ý cần citation dạng [Nguồn X].
3. Nếu không đủ bằng chứng, nói rõ phần chưa đủ.

CÂU HỎI GỐC: {query}
HOP 1 - CONTEXT: {context_string}
HOP 1 - ANSWER: {answer}
HOP 2 - REWRITTEN QUERY: {rewritten_query}
HOP 2 - CONTEXT: {context_hop2}
HOP 2 - ANSWER: {answer_hop2}
"""
                    answer = self.llm.invoke(synthesis_prompt)
                    llm_calls += 1  # Synthesis
                    
                    # Merge sources
                    combined_sources = sources + sources_hop2
                    sources = [dict(src, id=i) for i, src in enumerate(combined_sources, 1)]
                    confidence = 0.7
        
        # Format final answer
        rewritten_suffix = f"\nQuery rewrite: {rewritten_query}" if rewritten_query else ""
        answer_with_confidence = (
            f"{answer}\n\n"
            f"(Self-RAG dùng {hops_used} hop | Độ tự tin: {confidence:.0%})"
            f"{rewritten_suffix}"
        )
        
        benchmark = {
            "hops_used": hops_used,
            "confidence": round(confidence, 3),
            "rewritten_query": rewritten_query,
            "total_time_sec": round(time.perf_counter() - start_ts, 3),
            "early_stopped": early_stopped,
            "eval_skipped": False,
            "llm_calls": llm_calls,  # NEW: Track total LLM calls
        }
        return answer_with_confidence, sources, benchmark


# Backward compatibility
def get_answer_with_selfrag_citation(
    query: str,
    vector_db,
    chat_history: List[Dict] | None = None,
    confidence_threshold: float = 0.62,
    initial_k: int = 5,
    use_combined_prompt: bool = True,  # Phase 2: Default to combined prompt
) -> Tuple[str, List[Dict], Dict]:
    chain = SelfRAGChain()
    return chain.get_answer(
        query, vector_db, chat_history, confidence_threshold, 
        initial_k=initial_k, use_combined_prompt=use_combined_prompt
    )


# Export helper functions for rag_coordinator
_format_chat_history = BaseRAGChain.format_chat_history
_build_context_and_sources = BaseRAGChain.build_context_and_sources
def _answer_with_context(llm, query, context_str, ctx):
    from src.application.prompts import get_rag_prompt, get_rag_prompt_with_history
    if ctx:
        prompt = get_rag_prompt_with_history().format(
            chat_history=_format_chat_history(ctx),
            context=context_str,
            question=query,
        )
    else:
        prompt = get_rag_prompt().format(
            context=context_str,
            question=query,
        )
    return llm.invoke(prompt)

_extract_json_payload = SelfRAGChain._extract_json_payload

"""
src/utils/logger.py
───────────────────
Simple performance logging utility for RAG pipeline.
Logs timing and LLM call metrics to terminal.
"""

import time
from typing import Dict, Optional


class PerformanceLogger:
    """Simple logger for RAG pipeline performance metrics."""
    
    def __init__(self):
        self.llm_calls = 0
        self.start_time = None
        self.step_timings = {}
    
    def start(self):
        """Start timing the pipeline."""
        self.start_time = time.perf_counter()
        self.llm_calls = 0
        self.step_timings = {}
    
    def log_step(self, step_name: str, duration: float):
        """Log a pipeline step with its duration."""
        self.step_timings[step_name] = duration
        print(f"  ⏱️  {step_name}: {duration:.3f}s")
    
    def log_llm_call(self, purpose: str = "", temperature: float = None):
        """Log an LLM call."""
        self.llm_calls += 1
        temp_str = f", temp={temperature}" if temperature is not None else ""
        if purpose:
            print(f"  → LLM Call #{self.llm_calls}: {purpose}{temp_str}")
    
    def log_summary(self, debug_info: Optional[Dict] = None):
        """Log final summary with all metrics."""
        if self.start_time is None:
            return
        
        total_time = time.perf_counter() - self.start_time
        
        print(f"\n{'='*60}")
        print(f"PERFORMANCE SUMMARY")
        print(f"{'='*60}")
        
        # LLM calls
        print(f"LLM Calls: {self.llm_calls}")
        
        # Total time
        print(f"Total Time: {total_time:.3f}s")
        
        # Breakdown from debug_info if available
        if debug_info and "timing" in debug_info:
            print(f"\nDetailed Time Breakdown:")
            timing = debug_info["timing"]
            
            # Model loading (if tracked)
            if "llm_load" in timing:
                print(f"  • LLM Load: {timing['llm_load']:.3f}s")
            
            # Embedding (if tracked)
            if "embedding" in timing:
                print(f"  • Embedding: {timing['embedding']:.3f}s")
            
            # Retrieval breakdown
            retrieval_time = (
                timing.get("hybrid_retrieve") or 
                timing.get("semantic_retrieve") or
                0
            )
            if retrieval_time > 0:
                print(f"  • Retrieval Total: {retrieval_time:.3f}s")
                if "retriever_invoke" in timing:
                    print(f"    - Invoke (embed + search): {timing['retriever_invoke']:.3f}s")
            
            # Context building
            if "context_build" in timing:
                print(f"  • Context Building: {timing['context_build']:.3f}s")
            
            # Rewrite
            if "conv_rewrite" in timing:
                print(f"  • Query Rewrite: {timing['conv_rewrite']:.3f}s")
            
            # Re-rank
            if "rerank" in timing:
                print(f"  • Re-rank: {timing['rerank']:.3f}s")
            
            # Self-RAG
            if "selfrag" in timing:
                print(f"  • Self-RAG: {timing['selfrag']:.3f}s")
                if "hops_used" in debug_info:
                    print(f"    - Hops: {debug_info['hops_used']}")
                if "confidence" in debug_info:
                    print(f"    - Confidence: {debug_info['confidence']:.1%}")
            
            # LLM generation breakdown
            if "llm" in timing:
                print(f"  • Generation Total: {timing['llm']:.3f}s")
                if "llm_invoke" in timing:
                    print(f"    - LLM Invoke: {timing['llm_invoke']:.3f}s")
            
            # Multi-doc
            if "multidoc" in timing:
                print(f"  • Multi-doc: {timing['multidoc']:.3f}s")
        
        # Pipeline info
        if debug_info and "pipeline" in debug_info:
            print(f"\nPipeline: {debug_info['pipeline']}")
        
        # Rewrite info
        if debug_info and debug_info.get("rewrite_triggered"):
            print(f"\nQuery Rewrite: Triggered")
            if "rewritten_query" in debug_info:
                print(f"  Original: {debug_info.get('original_query', 'N/A')}")
                print(f"  Rewritten: {debug_info['rewritten_query']}")
        
        print(f"{'='*60}\n")


# Global logger instance
_logger = PerformanceLogger()


def get_logger() -> PerformanceLogger:
    """Get the global performance logger instance."""
    return _logger


def log_query_start(query: str):
    """Log the start of a query."""
    print(f"\n{'='*60}")
    print(f"Processing Query: {query[:50]}{'...' if len(query) > 50 else ''}")
    print(f"{'='*60}")
    _logger.start()


def log_query_end(debug_info: Optional[Dict] = None):
    """Log the end of a query with summary."""
    _logger.log_summary(debug_info)

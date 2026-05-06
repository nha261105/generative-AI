from typing import Dict, List, Set, Tuple
from functools import lru_cache
import hashlib
import re
import time
import streamlit as st  # NEW: Phase 2 - for @st.cache_data

from langchain_core.documents import Document
from src.application.chain_base import BaseRAGChain


STOPWORDS = {
    "và", "là", "của", "cho", "trong", "được", "các", "những", "một", "với",
    "the", "and", "for", "that", "this", "from", "are", "was", "were", "have",
}


class GraphRAGChain(BaseRAGChain):
    """
    GraphRAG chain với knowledge graph traversal.
    
    Xây dựng graph từ term co-occurrence, traverse 2-hop để expand context.
    """
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()
    
    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        words = re.findall(r"[\w\-]{3,}", GraphRAGChain._normalize_text(text))
        return {w for w in words if w not in STOPWORDS and len(w) >= 4}
    
    @staticmethod
    def _doc_key(doc: Document) -> str:
        source = str(doc.metadata.get("source") or doc.metadata.get("filename") or "")
        page = str(doc.metadata.get("page", ""))
        raw = f"{source}|{page}|{doc.page_content[:400]}"
        return hashlib.md5(raw.encode("utf-8", errors="ignore")).hexdigest()
    
    @staticmethod
    @st.cache_data(ttl=3600, show_spinner=False)  # Phase 2: Cache for 1 hour
    def _build_graph_index_cached(cache_key: str, payload: str) -> Dict:
        """
        Build graph index với Streamlit cache (persistent across queries).
        Cache for 1 hour to improve GraphRAG performance on repeated queries.
        """
        return GraphRAGChain._build_graph_index_internal(cache_key, payload)
    
    @staticmethod
    @lru_cache(maxsize=8)
    def _build_graph_index_internal(cache_key: str, payload: str) -> Dict:
        """Build graph index từ documents với term-based edges."""
        del cache_key
        
        rows = payload.split("\n\n<<DOC>>\n\n") if payload else []
        docs_meta: List[Dict] = []
        for row in rows:
            if not row.strip():
                continue
            parts = row.split("\n<<SEP>>\n", 3)
            if len(parts) != 4:
                continue
            key, source_file, raw_page, content = parts
            page = int(raw_page) if raw_page.isdigit() else -1
            terms = GraphRAGChain._tokenize(content)
            docs_meta.append({
                "key": key,
                "source_file": source_file,
                "page": page,
                "content": content,
                "terms": terms,
            })
        
        # Build term-to-doc index
        term_to_doc: Dict[str, List[int]] = {}
        for idx, node in enumerate(docs_meta):
            for term in node["terms"]:
                term_to_doc.setdefault(term, []).append(idx)
        
        # Build adjacency matrix
        adjacency: Dict[int, Dict[int, float]] = {i: {} for i in range(len(docs_meta))}
        
        # Edges from term co-occurrence
        for _, doc_indices in term_to_doc.items():
            if len(doc_indices) <= 1:
                continue
            limited = doc_indices[:25]
            for i in range(len(limited)):
                for j in range(i + 1, len(limited)):
                    a, b = limited[i], limited[j]
                    adjacency[a][b] = adjacency[a].get(b, 0.0) + 1.0
                    adjacency[b][a] = adjacency[b].get(a, 0.0) + 1.0
        
        # Bonus for same file and nearby pages
        for i, node_i in enumerate(docs_meta):
            for j, score in list(adjacency[i].items()):
                node_j = docs_meta[j]
                if node_i["source_file"] and node_i["source_file"] == node_j["source_file"]:
                    score += 0.8
                    if node_i["page"] >= 0 and node_j["page"] >= 0 and abs(node_i["page"] - node_j["page"]) <= 1:
                        score += 0.6
                adjacency[i][j] = score
        
        # Keep top neighbors
        top_neighbors: Dict[int, List[Tuple[int, float]]] = {}
        for i, neighbors in adjacency.items():
            ordered = sorted(neighbors.items(), key=lambda x: x[1], reverse=True)
            top_neighbors[i] = ordered[:6]  # OPTIMIZED: 8→6 neighbors (-25% traverse time)
        
        return {
            "docs_meta": docs_meta,
            "top_neighbors": top_neighbors,
        }
    
    @staticmethod
    def _get_all_docs_from_vector_store(vector_db) -> List[Document]:
        docstore = getattr(vector_db, "docstore", None)
        raw = getattr(docstore, "_dict", {}) if docstore is not None else {}
        return [doc for doc in raw.values() if isinstance(doc, Document)]
    
    @staticmethod
    def _make_graph_payload(docs: List[Document]) -> Tuple[str, Dict[str, int]]:
        rows: List[str] = []
        key_to_index: Dict[str, int] = {}
        for idx, doc in enumerate(docs):
            key = GraphRAGChain._doc_key(doc)
            key_to_index[key] = idx
            source_file = str(doc.metadata.get("filename") or doc.metadata.get("source") or "Tài liệu").split("/")[-1]
            page = doc.metadata.get("page", -1)
            page_int = page if isinstance(page, int) else -1
            content = str(doc.page_content or "").strip()
            rows.append(f"{key}\n<<SEP>>\n{source_file}\n<<SEP>>\n{page_int}\n<<SEP>>\n{content}")
        return "\n\n<<DOC>>\n\n".join(rows), key_to_index
    
    @staticmethod
    def _traverse_two_hops(
        seed_indices: List[int],
        top_neighbors: Dict[int, List[Tuple[int, float]]],
    ) -> Dict[int, float]:
        """2-hop graph traversal từ seed nodes."""
        scores: Dict[int, float] = {}
        
        for seed in seed_indices:
            scores[seed] = max(scores.get(seed, 0.0), 3.0)
        
        # Hop 1
        hop1_nodes: List[int] = []
        for seed in seed_indices:
            for nb, weight in top_neighbors.get(seed, []):
                hop1_nodes.append(nb)
                scores[nb] = max(scores.get(nb, 0.0), 2.0 + weight * 0.25)
        
        # Hop 2
        for node in hop1_nodes:
            for nb, weight in top_neighbors.get(node, []):
                scores[nb] = max(scores.get(nb, 0.0), 1.0 + weight * 0.2)
        
        return scores
    
    def _select_graphrag_docs(
        self,
        query: str,
        seed_docs: List[Document],
        all_docs: List[Document],
        top_k: int,
    ) -> Tuple[List[Document], Dict]:
        """Select documents bằng graph traversal."""
        payload, _ = self._make_graph_payload(all_docs)
        graph_key = hashlib.md5(payload.encode("utf-8", errors="ignore")).hexdigest()
        index = self._build_graph_index_cached(graph_key, payload)  # Phase 2: Use cached version
        docs_meta = index["docs_meta"]
        top_neighbors = index["top_neighbors"]
        
        key_to_meta_idx = {node["key"]: i for i, node in enumerate(docs_meta)}
        meta_idx_to_doc: Dict[int, Document] = {}
        for doc in all_docs:
            key = self._doc_key(doc)
            meta_idx = key_to_meta_idx.get(key)
            if meta_idx is not None and meta_idx not in meta_idx_to_doc:
                meta_idx_to_doc[meta_idx] = doc
        
        seed_indices: List[int] = []
        for doc in seed_docs:
            meta_idx = key_to_meta_idx.get(self._doc_key(doc))
            if meta_idx is not None:
                seed_indices.append(meta_idx)
        
        if not seed_indices:
            return seed_docs[:top_k], {
                "seed_count": len(seed_docs),
                "expanded_count": len(seed_docs),
                "graph_node_count": len(docs_meta),
                "graph_edge_count": sum(len(v) for v in top_neighbors.values()),
            }
        
        traversed_scores = self._traverse_two_hops(seed_indices, top_neighbors)
        query_terms = self._tokenize(query)
        
        ranked_indices: List[Tuple[int, float]] = []
        for meta_idx, base_score in traversed_scores.items():
            node = docs_meta[meta_idx]
            overlap = len(query_terms & node["terms"])
            final_score = base_score + overlap * 0.7
            ranked_indices.append((meta_idx, final_score))
        
        ranked_indices.sort(key=lambda x: x[1], reverse=True)
        selected_docs: List[Document] = []
        for meta_idx, _ in ranked_indices:
            doc = meta_idx_to_doc.get(meta_idx)
            if doc is None:
                continue
            selected_docs.append(doc)
            if len(selected_docs) >= top_k:
                break
        
        if not selected_docs:
            selected_docs = seed_docs[:top_k]
        
        return selected_docs, {
            "seed_count": len(seed_docs),
            "expanded_count": len(traversed_scores),
            "graph_node_count": len(docs_meta),
            "graph_edge_count": sum(len(v) for v in top_neighbors.values()),
        }
    
    def get_answer(
        self,
        query: str,
        vector_db,
        chat_history: List[Dict] | None = None,
        k: int = 4,
        fetch_k: int = 12,
    ) -> Tuple[str, List[Dict], Dict]:
        start_ts = time.perf_counter()
        
        # Initial retrieval
        retriever = vector_db.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k, "fetch_k": max(fetch_k, k * 3)},
        )
        seed_docs = retriever.invoke(query)
        
        # Graph expansion
        all_docs = self._get_all_docs_from_vector_store(vector_db)
        docs, graph_stats = self._select_graphrag_docs(query, seed_docs, all_docs, top_k=k)
        
        if not docs:
            response, sources = self.get_empty_response()
            return response, sources, {
                "retrieval_backend": "graph-traversal",
                "graph_enabled": True,
                "total_time_sec": round(time.perf_counter() - start_ts, 3),
            }
        
        context_string, sources = self.build_context_and_sources(docs)
        response = self.generate_answer(query, context_string, chat_history)
        
        return response, sources, {
            "retrieval_backend": "graph-traversal",
            "graph_enabled": True,
            "seed_count": graph_stats.get("seed_count", len(seed_docs)),
            "expanded_count": graph_stats.get("expanded_count", len(docs)),
            "graph_node_count": graph_stats.get("graph_node_count", len(all_docs)),
            "graph_edge_count": graph_stats.get("graph_edge_count", 0),
            "total_time_sec": round(time.perf_counter() - start_ts, 3),
        }


# Backward compatibility
def get_answer_with_graphrag_citation(
    query: str,
    vector_db,
    chat_history: List[Dict] | None = None,
    k: int = 4,
    fetch_k: int = 12,
) -> Tuple[str, List[Dict], Dict]:
    chain = GraphRAGChain()
    return chain.get_answer(query, vector_db, chat_history, k, fetch_k)

from typing import Dict, List, Set, Tuple
from functools import lru_cache
import hashlib
import re
import time

from langchain_community.llms import Ollama
from langchain_core.documents import Document

from src.application.prompts import get_rag_prompt, get_rag_prompt_with_history


STOPWORDS = {
    "và", "là", "của", "cho", "trong", "được", "các", "những", "một", "với",
    "the", "and", "for", "that", "this", "from", "are", "was", "were", "have",
}


def _format_chat_history(chat_history: List[Dict] | None, max_turns: int = 5) -> str:
    if not chat_history:
        return "(Chưa có lịch sử hội thoại)"

    recent_turns = chat_history[-max_turns:]
    lines: List[str] = []
    for turn in recent_turns:
        question = (turn.get("question") or "").strip()
        answer = (turn.get("answer") or "").strip()

        if question:
            lines.append(f"Người dùng: {question}")
        if answer:
            lines.append(f"Trợ lý: {answer}")

    return "\n".join(lines) if lines else "(Chưa có lịch sử hội thoại)"


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _tokenize(text: str) -> Set[str]:
    words = re.findall(r"[\w\-]{3,}", _normalize_text(text))
    return {w for w in words if w not in STOPWORDS and len(w) >= 4}


def _doc_key(doc: Document) -> str:
    source = str(doc.metadata.get("source") or doc.metadata.get("filename") or "")
    page = str(doc.metadata.get("page", ""))
    raw = f"{source}|{page}|{doc.page_content[:400]}"
    return hashlib.md5(raw.encode("utf-8", errors="ignore")).hexdigest()


@lru_cache(maxsize=8)
def _build_graph_index(cache_key: str, payload: str) -> Dict:
    # payload chứa dữ liệu tóm tắt để cache theo vector store instance.
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
        terms = _tokenize(content)
        docs_meta.append(
            {
                "key": key,
                "source_file": source_file,
                "page": page,
                "content": content,
                "terms": terms,
            }
        )

    term_to_doc: Dict[str, List[int]] = {}
    for idx, node in enumerate(docs_meta):
        for term in node["terms"]:
            term_to_doc.setdefault(term, []).append(idx)

    adjacency: Dict[int, Dict[int, float]] = {i: {} for i in range(len(docs_meta))}

    # Cạnh theo term chung.
    for _, doc_indices in term_to_doc.items():
        if len(doc_indices) <= 1:
            continue
        limited = doc_indices[:25]
        for i in range(len(limited)):
            for j in range(i + 1, len(limited)):
                a, b = limited[i], limited[j]
                adjacency[a][b] = adjacency[a].get(b, 0.0) + 1.0
                adjacency[b][a] = adjacency[b].get(a, 0.0) + 1.0

    # Cộng điểm nếu cùng file và gần trang.
    for i, node_i in enumerate(docs_meta):
        for j, score in list(adjacency[i].items()):
            node_j = docs_meta[j]
            if node_i["source_file"] and node_i["source_file"] == node_j["source_file"]:
                score += 0.8
                if node_i["page"] >= 0 and node_j["page"] >= 0 and abs(node_i["page"] - node_j["page"]) <= 1:
                    score += 0.6
            adjacency[i][j] = score

    # Giữ top neighbors để traversal nhanh và ổn định.
    top_neighbors: Dict[int, List[Tuple[int, float]]] = {}
    for i, neighbors in adjacency.items():
        ordered = sorted(neighbors.items(), key=lambda x: x[1], reverse=True)
        top_neighbors[i] = ordered[:8]

    return {
        "docs_meta": docs_meta,
        "top_neighbors": top_neighbors,
    }


def _get_all_docs_from_vector_store(vector_db) -> List[Document]:
    docstore = getattr(vector_db, "docstore", None)
    raw = getattr(docstore, "_dict", {}) if docstore is not None else {}
    return [doc for doc in raw.values() if isinstance(doc, Document)]


def _make_graph_payload(docs: List[Document]) -> Tuple[str, Dict[str, int]]:
    rows: List[str] = []
    key_to_index: Dict[str, int] = {}
    for idx, doc in enumerate(docs):
        key = _doc_key(doc)
        key_to_index[key] = idx
        source_file = str(doc.metadata.get("filename") or doc.metadata.get("source") or "Tài liệu").split("/")[-1]
        page = doc.metadata.get("page", -1)
        page_int = page if isinstance(page, int) else -1
        content = str(doc.page_content or "").strip()
        rows.append(f"{key}\n<<SEP>>\n{source_file}\n<<SEP>>\n{page_int}\n<<SEP>>\n{content}")
    return "\n\n<<DOC>>\n\n".join(rows), key_to_index


def _traverse_two_hops(
    seed_indices: List[int],
    top_neighbors: Dict[int, List[Tuple[int, float]]],
) -> Dict[int, float]:
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
    query: str,
    seed_docs: List[Document],
    all_docs: List[Document],
    top_k: int,
) -> Tuple[List[Document], Dict]:
    payload, _ = _make_graph_payload(all_docs)
    graph_key = hashlib.md5(payload.encode("utf-8", errors="ignore")).hexdigest()
    index = _build_graph_index(graph_key, payload)
    docs_meta = index["docs_meta"]
    top_neighbors = index["top_neighbors"]

    key_to_meta_idx = {node["key"]: i for i, node in enumerate(docs_meta)}
    meta_idx_to_doc: Dict[int, Document] = {}
    for doc in all_docs:
        key = _doc_key(doc)
        meta_idx = key_to_meta_idx.get(key)
        if meta_idx is not None and meta_idx not in meta_idx_to_doc:
            meta_idx_to_doc[meta_idx] = doc

    seed_indices: List[int] = []
    for doc in seed_docs:
        meta_idx = key_to_meta_idx.get(_doc_key(doc))
        if meta_idx is not None:
            seed_indices.append(meta_idx)

    if not seed_indices:
        return seed_docs[:top_k], {
            "seed_count": len(seed_docs),
            "expanded_count": len(seed_docs),
            "graph_node_count": len(docs_meta),
            "graph_edge_count": sum(len(v) for v in top_neighbors.values()),
        }

    traversed_scores = _traverse_two_hops(seed_indices, top_neighbors)
    query_terms = _tokenize(query)

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


def get_answer_with_graphrag_citation(
    query: str,
    vector_db,
    chat_history: List[Dict] | None = None,
    k: int = 4,
    fetch_k: int = 12,
) -> Tuple[str, List[Dict], Dict]:
    start_ts = time.perf_counter()
    llm = Ollama(
        model="qwen2.5:7b",
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
    )

    retriever = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": max(fetch_k, k * 3)},
    )
    seed_docs = retriever.invoke(query)

    all_docs = _get_all_docs_from_vector_store(vector_db)
    docs, graph_stats = _select_graphrag_docs(
        query=query,
        seed_docs=seed_docs,
        all_docs=all_docs,
        top_k=k,
    )

    if not docs:
        return (
            "Mình chưa tìm thấy ngữ cảnh phù hợp trong tài liệu hiện tại.",
            [
                {
                    "id": 1,
                    "page": "?",
                    "content": "Không tìm thấy đoạn trích phù hợp.",
                    "source_file": "Không xác định",
                }
            ],
            {
                "retrieval_backend": "graph-traversal",
                "graph_enabled": True,
                "total_time_sec": round(time.perf_counter() - start_ts, 3),
            },
        )

    context_list: List[str] = []
    sources: List[Dict] = []

    for i, doc in enumerate(docs, start=1):
        raw_page = doc.metadata.get("page", 0)
        page_num = raw_page + 1 if isinstance(raw_page, int) else (raw_page or "?")
        source_file = str(
            doc.metadata.get("filename")
            or doc.metadata.get("source")
            or "Tài liệu"
        ).split("/")[-1]

        context_list.append(f"[Nguồn {i} | Trang {page_num}]: {doc.page_content}")
        sources.append(
            {
                "id": i,
                "page": page_num,
                "content": doc.page_content,
                "source_file": source_file,
            }
        )

    context_string = "\n\n".join(context_list)

    if chat_history:
        prompt = get_rag_prompt_with_history().format(
            chat_history=_format_chat_history(chat_history),
            context=context_string,
            question=query,
        )
    else:
        prompt = get_rag_prompt().format(
            context=context_string,
            question=query,
        )

    response = llm.invoke(prompt)

    return (
        response,
        sources,
        {
            "retrieval_backend": "graph-traversal",
            "graph_enabled": True,
            "seed_count": graph_stats.get("seed_count", len(seed_docs)),
            "expanded_count": graph_stats.get("expanded_count", len(docs)),
            "graph_node_count": graph_stats.get("graph_node_count", len(all_docs)),
            "graph_edge_count": graph_stats.get("graph_edge_count", 0),
            "total_time_sec": round(time.perf_counter() - start_ts, 3),
        },
    )

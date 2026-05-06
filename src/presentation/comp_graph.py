"""
src/presentation/comp_graph.py
────────────────────────────────
Knowledge graph visualization dùng pyvis.

Nhận networkx graph (build từ FAISS docstore) và render ra HTML tương tác.
Node tô màu theo type, edge hiển thị label quan hệ khi hover.
"""

from __future__ import annotations

import hashlib
import re
from typing import TYPE_CHECKING

import streamlit as st
import streamlit.components.v1 as components

if TYPE_CHECKING:
    import networkx as nx

# Màu theo node type
_NODE_COLORS: dict[str, str] = {
    "Person":  "#10A37F",   # xanh lá — accent
    "Org":     "#3B82F6",   # xanh dương
    "Concept": "#F59E0B",   # vàng cam
    "default": "#9B9B9B",   # xám
}

_NODE_SIZES: dict[str, int] = {
    "Person":  22,
    "Org":     26,
    "Concept": 18,
    "default": 16,
}


def _build_pyvis_html(graph: "nx.Graph", height: str = "500px") -> str:
    """
    Convert networkx graph → pyvis HTML string.

    Dùng pyvis Network trực tiếp thay vì from_nx() để kiểm soát
    màu sắc, size, tooltip theo node type.
    """
    try:
        from pyvis.network import Network
    except ImportError:
        return "<p style='color:red'>pyvis chưa được cài. Chạy: pip install pyvis</p>"

    net = Network(
        height=height,
        width="100%",
        bgcolor="#1E1E1E",
        font_color="#D1D1D1",
        directed=graph.is_directed() if hasattr(graph, "is_directed") else False,
    )
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=120)

    # Thêm nodes
    for node_id, attrs in graph.nodes(data=True):
        node_type = attrs.get("type", "default")
        color = _NODE_COLORS.get(node_type, _NODE_COLORS["default"])
        size = _NODE_SIZES.get(node_type, _NODE_SIZES["default"])
        label = str(node_id)
        # Tooltip hiển thị type + bất kỳ metadata nào có
        title_parts = [f"<b>{label}</b>", f"Type: {node_type}"]
        for k, v in attrs.items():
            if k not in ("type",):
                title_parts.append(f"{k}: {v}")
        net.add_node(
            str(node_id),
            label=label,
            color=color,
            size=size,
            title="<br>".join(title_parts),
            font={"size": 11, "color": "#ECECEC"},
        )

    # Thêm edges
    for src, dst, attrs in graph.edges(data=True):
        relation = attrs.get("relation", attrs.get("label", ""))
        weight = float(attrs.get("weight", 1.0))
        width = max(1.0, min(5.0, weight * 0.5))
        net.add_edge(
            str(src),
            str(dst),
            title=relation or "liên quan",
            label=relation[:30] if relation else "",
            width=width,
            color={"color": "#555", "highlight": "#10A37F"},
            font={"size": 9, "color": "#9B9B9B", "align": "middle"},
        )

    # Options JSON để tắt physics sau khi stabilize
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "stabilization": { "iterations": 150, "fit": true },
        "barnesHut": { "damping": 0.4 }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true,
        "keyboard": true
      },
      "edges": {
        "smooth": { "type": "dynamic" }
      }
    }
    """)

    return net.generate_html()


def _build_graph_from_vector_store(vector_db) -> "nx.Graph | None":
    """
    Build networkx graph từ FAISS docstore.
    Dùng lại logic term-overlap của chain_graphrag để tạo edges.
    Chỉ lấy top 200 nodes để tránh render quá nặng.
    """
    try:
        import networkx as nx
        from langchain_core.documents import Document
    except ImportError:
        return None

    docstore = getattr(vector_db, "docstore", None)
    if docstore is None:
        return None
    raw_dict = getattr(docstore, "_dict", {})
    docs = [d for d in raw_dict.values() if isinstance(d, Document)]

    if not docs:
        return None

    # Lấy tối đa 200 docs để tránh graph quá lớn
    docs = docs[:200]

    G = nx.Graph()
    stopwords = {
        "và", "là", "của", "cho", "trong", "được", "các", "những", "một", "với",
        "the", "and", "for", "that", "this", "from", "are", "was", "were", "have",
    }

    def _terms(text: str) -> set[str]:
        words = re.findall(r"[\w\-]{4,}", text.lower())
        return {w for w in words if w not in stopwords}

    # Nodes = unique filenames (Org) + top terms (Concept)
    file_nodes: dict[str, str] = {}  # filename → node_id
    for doc in docs:
        fname = str(doc.metadata.get("filename") or doc.metadata.get("source") or "").split("/")[-1]
        if fname and fname not in file_nodes:
            file_nodes[fname] = fname
            G.add_node(fname, type="Org")

    # Term frequency để chọn top terms làm Concept nodes
    term_freq: dict[str, int] = {}
    doc_terms: list[set[str]] = []
    for doc in docs:
        t = _terms(doc.page_content)
        doc_terms.append(t)
        for w in t:
            term_freq[w] = term_freq.get(w, 0) + 1

    # Chỉ lấy terms xuất hiện >= 3 lần, top 60
    top_terms = sorted(
        [w for w, c in term_freq.items() if c >= 3],
        key=lambda w: term_freq[w],
        reverse=True,
    )[:60]

    for term in top_terms:
        G.add_node(term, type="Concept")

    # Edges: doc → file (Org), doc terms → Concept nodes
    for i, doc in enumerate(docs):
        fname = str(doc.metadata.get("filename") or doc.metadata.get("source") or "").split("/")[-1]
        page = doc.metadata.get("page", 0)
        t = doc_terms[i]

        for term in t:
            if term in top_terms:
                if G.has_node(fname) and G.has_node(term):
                    if G.has_edge(fname, term):
                        G[fname][term]["weight"] = G[fname][term].get("weight", 1) + 1
                    else:
                        G.add_edge(fname, term, relation="chứa khái niệm", weight=1)

        # Edges giữa Concept nodes có term overlap trong cùng doc
        term_list = [t_ for t_ in t if t_ in top_terms]
        for a in range(len(term_list)):
            for b in range(a + 1, min(a + 4, len(term_list))):
                ta, tb = term_list[a], term_list[b]
                if G.has_node(ta) and G.has_node(tb):
                    if G.has_edge(ta, tb):
                        G[ta][tb]["weight"] = G[ta][tb].get("weight", 1) + 0.5
                    else:
                        G.add_edge(ta, tb, relation="đồng xuất hiện", weight=0.5)

    # Xóa isolated nodes
    isolated = [n for n in G.nodes() if G.degree(n) == 0]
    G.remove_nodes_from(isolated)

    return G if G.number_of_nodes() > 0 else None


def render_graph(graph: "nx.Graph | None", height: str = "500px") -> None:
    """
    Render knowledge graph tương tác.
    Nhận networkx graph hoặc None (sẽ hiển thị empty state).
    """
    if graph is None or graph.number_of_nodes() == 0:
        st.info("Chưa có dữ liệu graph. Upload tài liệu để xem knowledge graph.")
        return

    n_nodes = graph.number_of_nodes()
    n_edges = graph.number_of_edges()
    st.caption(f"🔵 {n_nodes} nodes · 🔗 {n_edges} edges")

    html_str = _build_pyvis_html(graph, height=height)
    # Dùng height + 20px để tránh scrollbar trong iframe
    px_height = int(height.replace("px", "")) + 20
    components.html(html_str, height=px_height, scrolling=False)


def get_graph_stats(vector_db) -> dict:
    """Trả về stats graph để hiển thị trên sidebar."""
    if vector_db is None:
        return {"nodes": 0, "edges": 0}
    g = _build_graph_from_vector_store(vector_db)
    if g is None:
        return {"nodes": 0, "edges": 0}
    return {"nodes": g.number_of_nodes(), "edges": g.number_of_edges()}


def render_graph_from_vector_store(vector_db, height: str = "500px") -> None:
    """Convenience wrapper: build graph từ vector_db rồi render."""
    graph = _build_graph_from_vector_store(vector_db)
    render_graph(graph, height=height)

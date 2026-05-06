"""
src/utils/doc_helpers.py
─────────────────────────
Unified helpers for document processing to eliminate code duplication.
"""

from typing import Dict, List


def doc_snippet(doc, max_len: int = 120) -> Dict:
    """
    Build a debug-friendly doc dict with file, page, and snippet.
    
    Args:
        doc: Document object with metadata and page_content
        max_len: Maximum length of snippet text
    
    Returns:
        Dict with keys: file, page, snippet
    """
    meta = doc.metadata or {}
    raw_page = meta.get("page", 0)
    page = raw_page + 1 if isinstance(raw_page, int) else (raw_page or "?")
    fname = str(meta.get("filename") or meta.get("source") or "?").split("/")[-1]
    text = (doc.page_content or "")[:max_len].replace("\n", " ")
    return {"file": fname, "page": page, "snippet": text}


def normalize_sources(raw_sources) -> List[Dict]:
    """
    Normalize sources to consistent schema.
    
    Args:
        raw_sources: List of source objects (dict or string)
    
    Returns:
        List of normalized source dicts with keys: id, page, content, source_file
    """
    out = []
    for i, s in enumerate(raw_sources or [], 1):
        if isinstance(s, dict):
            out.append({
                "id": s.get("id", i),
                "page": s.get("page", "?"),
                "content": str(s.get("content", "")).strip(),
                "source_file": s.get("source_file", "Tài liệu")
            })
        else:
            txt = str(s).strip()
            sf, pg = "Tài liệu", "?"
            if " - Trang " in txt:
                sf, _, pg = txt.partition(" - Trang ")
                sf = sf.strip() or "Tài liệu"
                pg = pg.strip() or "?"
            out.append({
                "id": i,
                "page": pg,
                "content": txt,
                "source_file": sf
            })
    return out


def build_source_text(sources: List[Dict]) -> str:
    """
    Build human-readable source text from normalized sources.
    
    Args:
        sources: List of normalized source dicts
    
    Returns:
        String like "Nguồn: file1.pdf — Trang 3, file2.pdf — Trang 5"
    """
    labels = []
    for s in sources:
        sf = str(s.get("source_file", "Tài liệu")).strip() or "Tài liệu"
        pg = s.get("page")
        labels.append(f"{sf} — Trang {pg}" if pg not in (None, "", "?") else sf)
    return "Nguồn: " + (", ".join(dict.fromkeys(labels)) or "N/A")

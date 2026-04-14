import streamlit as st
import re
from st_copy_to_clipboard import st_copy_to_clipboard
def highlight_by_query(content: str, query: str):
    words = query.split()
    
    for w in words:
        if len(w) < 3:
            continue

        pattern = re.compile(f"({re.escape(w)})", re.IGNORECASE)
        content = pattern.sub(r"<mark>\1</mark>", content)

    return content


def clean_content(text: str):
    # Xóa xuống dòng thừa
    text = text.replace("\n", " ")

    # Xóa khoảng trắng dư
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def render_answer(answer: dict):
    """Render câu trả lời + citation + highlight"""

    # ===== 2. Hiển thị câu trả lời =====
    st.markdown(f"""
        <div class="answer-card">
            <div class="answer-badge">🤖 Trả lời</div>
            <p class="answer-text">{answer["text"]}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div title="Sao chép">', unsafe_allow_html=True)
    st_copy_to_clipboard(answer["text"])
    st.markdown('</div>', unsafe_allow_html=True)

    # ===== 3. Hiển thị vùng copy =====
    if st.session_state.get("show_copy", False):
        st.text_area(
            "Sao chép nội dung bên dưới:",
            value=answer["text"],
            height=150
        )


    # ===== 3. Hiển thị danh sách nguồn =====
    if "sources" in answer and answer["sources"]:
        st.write("---")
        st.write("📖 **Nguồn trích dẫn:**")

        query = answer.get('query',"")
        for i, src in enumerate(answer["sources"]):
            source_id = i + 1

            # Highlight nội dung
            content = clean_content(src["content"])

            highlighted = highlight_by_query(content, query)

            with st.expander(
                f"📍 Nguồn {source_id} | {src.get('source_file', 'Tài liệu')} | Trang {src['page']}"
            ):
                st.markdown(f"""
                <div class="highlight-box">
                    {highlighted}
                </div>
                """, unsafe_allow_html=True)

                st.caption(f"ID: {src['id']}")

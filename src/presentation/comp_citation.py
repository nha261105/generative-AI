import streamlit as st
import re
from st_copy_to_clipboard import st_copy_to_clipboard
from difflib import SequenceMatcher

def highlight_best_sentence(content: str, answer: str, source_id: int):
    # 1. Tách content gốc thành các câu
    source_sentences = re.split(r'(?<=[.!?])\s+', content)
    
    # 2. Tách answer thành các câu để tìm câu có chứa [Nguồn X] tương ứng
    answer_sentences = re.split(r'(?<=[.!?\n])\s+', answer)
    
    # Lọc ra những câu trong câu trả lời có chứa tag của Nguồn hiện tại
    target_claims = [s for s in answer_sentences if f"[Nguồn {source_id}]" in s]
    
    # Nếu LLM quên gắn tag, fallback: dùng tất cả các câu trong answer
    if not target_claims:
        target_claims = answer_sentences

    best_source_sentences = set()

    # 3. So khớp từng câu claim với các câu trong source
    for claim in target_claims:
        # Xóa tag [Nguồn X] để so khớp phần chữ chính xác hơn
        clean_claim = re.sub(r'\[Nguồn \d+\]', '', claim).strip()
        if len(clean_claim) < 10: # Bỏ qua các câu quá ngắn
            continue

        best = ""
        best_score = 0
        
        for s in source_sentences:
            s_clean = s.strip() # strip() remove specific leading and trailing characters from a string
            if len(s_clean) < 10: continue
            
            # So sánh độ tương đồng
            score = SequenceMatcher(None, s_clean.lower(), clean_claim.lower()).ratio()
            if score > best_score:
                best_score = score
                best = s_clean
        
        # Ngưỡng chấp nhận: 0.3 (30% giống nhau) là mức khá an toàn với AI viết lại
        if best_score > 0.30 and best:
            best_source_sentences.add(best)

    # 4. Highlight các câu đã tìm được trong content
    highlighted_content = content
    for best in best_source_sentences:
        highlighted_content = highlighted_content.replace(best, f"<mark>{best}</mark>")

    return highlighted_content


def clean_content(text: str):
    # Xóa xuống dòng thừa
    text = text.replace("\n", " ")

    # Xóa khoảng trắng dư
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def render_answer_with_citation(answer: dict):
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

    # # ===== 3. Hiển thị vùng copy =====
    # if st.session_state.get("show_copy", False):
    #     st.text_area(
    #         "Sao chép nội dung bên dưới:",
    #         value=answer["text"],
    #         height=150
    #     )


    # ===== 3. Hiển thị danh sách nguồn =====
    if "sources" in answer and answer["sources"]:
        st.write("---")
        st.write("📖 **Nguồn trích dẫn:**")
        
        for i, src in enumerate(answer["sources"]):
            source_id = i + 1

            # Highlight nội dung
            answer_text = answer["text"]
            content = clean_content(src["content"])

            highlighted = highlight_best_sentence(content, answer_text,source_id)

            with st.expander(
                f"📍 Nguồn {source_id} | {src.get('source_file', 'Tài liệu')} | Trang {src['page']}"
            ):
                st.markdown(f"""
                <div class="highlight-box">
                    {highlighted}
                </div>
                """, unsafe_allow_html=True)

                # st.caption(f"ID: {src['id']}")

def get_css(dark_mode: bool = False, sidebar_collapsed: bool = False) -> str:
    """ChatGPT-inspired CSS. Supports light/dark theme."""
    bg       = "#212121" if dark_mode else "#F7F7F8"
    panel    = "#2F2F2F" if dark_mode else "#FFFFFF"
    text     = "#ECECEC" if dark_mode else "#1A1A1A"
    subtext  = "#9B9B9B" if dark_mode else "#6B6B6B"
    border   = "#3E3E3E" if dark_mode else "#E0E0E0"
    sidebar_bg = "#171717" if dark_mode else "#1E1E1E"
    input_bg   = "#2F2F2F" if dark_mode else "#FFFFFF"
    input_ph   = "#777"   if dark_mode else "#999"
    accent     = "#10A37F"
    user_bg    = "#2F2F2F" if dark_mode else "#F0F0F0"
    assist_bg  = "transparent"

    sidebar_css = ""
    if sidebar_collapsed:
        sidebar_css = """
section[data-testid="stSidebar"] { margin-left: -22rem !important; }
"""

    css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Reset ────────────────────────────────────────── */
html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, sans-serif;
    background: __BG__;
    color: __TEXT__;
}
h1,h2,h3 { font-family: 'Inter', sans-serif; }
div[data-testid="stSidebarHeader"],
div[data-testid="stToolbar"],
header[data-testid="stHeader"] { display: none !important; }

div[data-testid="stMainBlockContainer"] {
    padding: 0.6rem 1rem 6rem;
    max-width: 820px;
    margin: 0 auto;
}

/* ── Sidebar ──────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: __SIDEBAR_BG__ !important;
    border-right: 1px solid rgba(255,255,255,0.08);
    padding: 0.8rem 0.6rem;
    transition: margin-left .2s ease;
}
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] label { color: #D1D1D1 !important; }

.sidebar-title {
    font-size: 0.95rem; font-weight: 700; color: #FFF !important;
    padding: 0.25rem 0.3rem 0.6rem;
}
.sidebar-section-label {
    font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.12em;
    color: #888 !important; font-weight: 700;
    margin: 1rem 0 0.4rem; padding: 0 0.2rem;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    border-radius: 0.5rem !important; min-height: 2.2rem !important;
    background: __ACCENT__ !important; border: none !important;
    color: #FFF !important; font-weight: 600 !important;
    text-align: left !important; justify-content: flex-start !important;
    padding: 0.4rem 0.65rem !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    filter: brightness(1.1);
}
section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    border-radius: 0.5rem !important; min-height: 2rem !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #D1D1D1 !important; font-weight: 500 !important;
    text-align: left !important; justify-content: flex-start !important;
    padding: 0.4rem 0.65rem !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.12) !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="tertiary"] {
    background: transparent !important; border: none !important;
    color: #999 !important; min-height: 1.8rem !important;
    padding: 0 0.2rem !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="tertiary"]:hover {
    color: #FFF !important;
}

/* Sidebar chat list */
.empty-chat-chip {
    font-size: 0.78rem; color: #777 !important;
    padding: 0.5rem; text-align: center;
    border: 1px dashed rgba(255,255,255,0.12); border-radius: 0.5rem;
}
.sidebar-history-summary {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.3rem 0.4rem; margin: 0 0 0.5rem;
    font-size: 0.68rem; color: #888 !important;
}
.sidebar-chat-subtitle {
    margin-top: -0.1rem; margin-bottom: 0.4rem;
    padding: 0.2rem 0.4rem; border-radius: 0.4rem;
    font-size: 0.64rem; color: #888 !important;
}
.sidebar-chat-subtitle.active { color: __ACCENT__ !important; }
.sidebar-chat-subtitle-text { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] .stCaption p { color: #999 !important; font-size: 0.72rem !important; }

/* Sidebar select/multiselect */
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #D1D1D1 !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] div,
section[data-testid="stSidebar"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] svg,
section[data-testid="stSidebar"] [data-baseweb="select"] input {
    color: #D1D1D1 !important; fill: #D1D1D1 !important;
}
div[role="listbox"] { background: #2A2A2A !important; border: 1px solid #444 !important; }
div[role="listbox"] [role="option"], div[role="listbox"] * { color: #D1D1D1 !important; }
div[role="listbox"] [aria-selected="true"] { background: rgba(16,163,127,0.18) !important; }

/* Sidebar file uploader */
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] > label { display: none; }
section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] {
    border: 1px dashed rgba(255,255,255,0.2) !important;
    background: rgba(255,255,255,0.04) !important;
    border-radius: 0.5rem !important;
    padding: 0.8rem 0.5rem !important;
    min-height: 60px !important;
}
section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"]:hover {
    border-color: __ACCENT__ !important;
    background: rgba(16,163,127,0.06) !important;
}
section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"]
  [data-testid="stFileUploaderDropzoneInstructions"] {
    font-size: 0 !important; color: transparent !important;
}
section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"]
  [data-testid="stFileUploaderDropzoneInstructions"]::before {
    content: "Kéo thả PDF vào đây"; display: block;
    font-size: 0.78rem; font-weight: 600; color: #AAA;
}
section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"]
  [data-testid="stFileUploaderDropzoneInstructions"] small { display: none !important; }
section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] button {
    border-radius: 0.4rem !important;
    border: 1px solid __ACCENT__ !important;
    background: __ACCENT__ !important;
    color: #FFF !important; font-weight: 600 !important;
    padding: 0.3rem 0.6rem !important;
}
section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] button > div {
    font-size: 0 !important;
}
section[data-testid="stSidebar"] section[data-testid="stFileUploaderDropzone"] button > div::after {
    content: "Chọn file"; font-size: 0.78rem;
}

/* ── Main header ──────────────────────────────────── */
.main-header {
    text-align: center; padding: 0.3rem 0 0.5rem;
}
.main-header h1 {
    font-size: 1.1rem; font-weight: 700; color: __TEXT__; margin: 0;
}
.main-header p {
    color: __SUBTEXT__; font-size: 0.78rem; margin: 0.15rem 0 0;
}

/* ── Status bar ───────────────────────────────────── */
.status-bar {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.4rem 0.7rem; margin: 0.3rem 0 0.6rem;
    background: __PANEL__; border: 1px solid __BORDER__;
    border-radius: 0.5rem; font-size: 0.74rem; color: __SUBTEXT__;
}
.status-dot {
    width: 6px; height: 6px; border-radius: 50%;
    display: inline-block;
}
.status-dot.ready { background: __ACCENT__; }
.status-dot.pending { background: #777; }
.status-dot.processing { background: #F59E0B; animation: pulse 1s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

/* ── Chat messages ────────────────────────────────── */
div[data-testid="stChatMessage"] {
    padding: 0.8rem 0 !important;
    border-bottom: 1px solid __BORDER__;
    max-width: 100%;
}
div[data-testid="stChatMessage"]:last-child { border-bottom: none; }

/* ── Answer card (used for comparisons) ───────────── */
.answer-card {
    background: __PANEL__; border: 1px solid __BORDER__;
    border-radius: 0.6rem; padding: 1rem; margin-top: 0.6rem;
    position: relative;
}
.answer-badge {
    position: absolute; top: -0.55rem; left: 0.8rem;
    background: __ACCENT__; color: #FFF;
    padding: 0.1rem 0.55rem; border-radius: 1rem;
    font-size: 0.6rem; font-weight: 700;
    letter-spacing: 0.05em; text-transform: uppercase;
}
.answer-text {
    font-size: 0.88rem; line-height: 1.65; color: __TEXT__;
    margin: 0.3rem 0 0.5rem;
}
.answer-source {
    padding-top: 0.5rem; border-top: 1px solid __BORDER__;
    font-size: 0.7rem; font-weight: 500; color: __SUBTEXT__;
}

/* ── Citation / Sources ───────────────────────────── */
.citation-header {
    font-size: 0.72rem; font-weight: 600; color: __SUBTEXT__;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin: 0.8rem 0 0.35rem; padding: 0;
}
.source-chip {
    display: inline-flex; align-items: center; gap: 0.3rem;
    background: __PANEL__; border: 1px solid __BORDER__;
    border-radius: 0.4rem; padding: 0.25rem 0.55rem;
    font-size: 0.72rem; color: __TEXT__; margin: 0.15rem 0.15rem 0.15rem 0;
    cursor: pointer; transition: border-color .15s;
}
.source-chip:hover { border-color: __ACCENT__; }
.source-chip .sc-label { font-weight: 600; color: __ACCENT__; }
.source-chip .sc-file  { color: __TEXT__; }
.source-chip .sc-page  { color: __SUBTEXT__; }

.highlight-box {
    background: rgba(16,163,127,0.06);
    border-left: 3px solid __ACCENT__;
    padding: 0.6rem 0.8rem;
    border-radius: 0 0.4rem 0.4rem 0;
    font-size: 0.82rem; line-height: 1.6; color: __TEXT__;
    margin: 0.2rem 0;
}
.highlight-box mark {
    background: rgba(16,163,127,0.25);
    color: inherit; padding: 0.05rem 0.15rem; border-radius: 2px;
}

/* ── Compare split view ───────────────────────────── */
.compare-header {
    text-align: center; font-size: 0.8rem; font-weight: 600;
    color: __SUBTEXT__; margin: 0.6rem 0 0.3rem;
}
.compare-stats {
    text-align: center; font-size: 0.68rem; color: __SUBTEXT__;
    margin-bottom: 0.4rem;
}

/* ── Input area ───────────────────────────────────── */
.qa-input-wrap {
    margin-top: 1rem;
}
div[data-testid="stTextInput"] > div > div > input {
    border-radius: 1.2rem !important;
    padding: 0.75rem 1rem !important;
    background: __INPUT_BG__ !important;
    border: 1px solid __BORDER__ !important;
    font-size: 0.88rem !important;
    color: __TEXT__ !important;
}
div[data-testid="stTextInput"] > div > div > input::placeholder {
    color: __INPUT_PH__ !important;
}
div[data-testid="stTextInput"] > div > div > input:focus {
    border-color: __ACCENT__ !important;
    box-shadow: 0 0 0 2px rgba(16,163,127,0.15) !important;
}

/* ── Buttons (main) ───────────────────────────────── */
.stButton > button {
    border-radius: 1.2rem !important; font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all .15s ease !important;
}
.stButton > button[kind="primary"] {
    background: __ACCENT__ !important;
    border: 1px solid __ACCENT__ !important;
    color: #FFF !important;
}
.stButton > button[kind="primary"]:hover {
    filter: brightness(1.1);
}
.stButton > button[kind="secondary"] {
    background: __PANEL__ !important;
    border: 1px solid __BORDER__ !important;
    color: __TEXT__ !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: __ACCENT__ !important;
}

/* ── Toggle ───────────────────────────────────────── */
.stToggle label, .stToggle label span {
    color: __TEXT__ !important; font-weight: 500 !important; font-size: 0.82rem !important;
}

/* ── Debug panel ──────────────────────────────────── */
.debug-doc {
    background: __PANEL__; border: 1px solid __BORDER__;
    border-radius: 0.4rem; padding: 0.45rem 0.6rem;
    margin: 0.3rem 0; font-size: 0.75rem; color: __TEXT__;
}
.debug-doc.reranked {
    border-left: 3px solid __ACCENT__;
}
.debug-doc-label {
    font-weight: 600; color: __ACCENT__; font-size: 0.72rem;
}
.debug-doc-text {
    color: __SUBTEXT__; margin-top: 0.2rem; font-size: 0.72rem;
    line-height: 1.4; max-height: 3.2em; overflow: hidden;
    text-overflow: ellipsis;
}

/* ── Misc ─────────────────────────────────────────── */
div[data-testid="stSidebarUserContent"] { padding-bottom: 0.8rem !important; }

__SIDEBAR_CSS__
</style>
"""
    return (
        css.replace("__BG__", bg).replace("__PANEL__", panel)
        .replace("__TEXT__", text).replace("__SUBTEXT__", subtext)
        .replace("__BORDER__", border).replace("__SIDEBAR_BG__", sidebar_bg)
        .replace("__INPUT_BG__", input_bg).replace("__INPUT_PH__", input_ph)
        .replace("__ACCENT__", accent).replace("__USER_BG__", user_bg)
        .replace("__ASSIST_BG__", assist_bg).replace("__SIDEBAR_CSS__", sidebar_css)
    )

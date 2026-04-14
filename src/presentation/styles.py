def get_css(dark_mode: bool = False, sidebar_collapsed: bool = False) -> str:
    """Return CSS by theme and sidebar visibility."""
    bg = "rgb(44, 44, 44)" if dark_mode else "#F4EFE8"
    panel = "rgb(52, 52, 52)" if dark_mode else "#FBF8F3"
    text = "#FFFFFF" if dark_mode else "#2D2926"
    subtext = "#A0A0A0" if dark_mode else "#6E6258"
    border = "#575757" if dark_mode else "#D7CCC1"
    sidebar_bg = "rgb(33, 33, 33)" if dark_mode else "#E6DED3"
    input_bg = "rgb(48, 48, 48)" if dark_mode else "#FFFFFF"
    input_placeholder = "#7A7A7A" if dark_mode else "#999999"

    sidebar_css = ""
    if sidebar_collapsed:
        sidebar_css = """
section[data-testid=\"stSidebar\"] {
    margin-left: -22rem !important;
}
"""

    css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    background: __BG__;
    color: __TEXT__;
}
h1, h2, h3, .font-headline {
    font-family: 'Plus Jakarta Sans', sans-serif;
}
div[data-testid="stSidebarHeader"], div[data-testid="stToolbar"] {
    display: none !important;
}
div[data-testid="stMainBlockContainer"] {
    padding-top: 0.8rem;
    padding-bottom: 1.2rem;
    max-width: 980px;
}

section[data-testid="stSidebar"] {
    background-color: __SIDEBAR_BG__ !important;
    border-right: 1px solid __BORDER__;
    padding: 1rem 0.75rem;
    transition: margin-left 0.2s ease;
}

section[data-testid="stSidebar"] .stButton > button[kind="tertiary"] {
    background: transparent !important;
    border: none !important;
    color: __TEXT__ !important;
    min-height: 2rem !important;
    padding: 0.1rem 0.25rem !important;
}

section[data-testid="stSidebar"] .stButton > button[kind="tertiary"]:hover {
    background: transparent !important;
    border: none !important;
    color: __TEXT__ !important;
}
section[data-testid="stSidebar"] * {
    color: __TEXT__ !important;
}
section[data-testid="stSidebar"] .sidebar-title {
    font-size: 1.05rem;
    font-weight: 800;
    padding: 0.35rem 0.35rem 0.8rem;
}
.sidebar-section-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: __SUBTEXT__ !important;
    font-weight: 700;
    margin-top: 1.2rem;
    margin-bottom: 0.8rem;
    padding: 0 0.2rem;
}
.empty-chat-chip {
    font-size: 0.85rem;
    color: __SUBTEXT__ !important;
    padding: 0.5rem 0.2rem;
}

section[data-testid="stSidebar"] .stCaption {
    color: __SUBTEXT__ !important;
    font-size: 0.74rem !important;
}
section[data-testid="stSidebar"] .stCaption p {
    color: __SUBTEXT__ !important;
}

header[data-testid="stHeader"] {
    z-index: 0;
}
.main-header {
    display: flex;
    align-items: center;
    padding: 0.4rem 0 0.8rem;
}
.main-header h1 {
    font-size: 1.25rem;
    font-weight: 800;
    color: __TEXT__;
    line-height: 1;
    margin: 0;
}
.main-header p {
    color: __SUBTEXT__;
    font-size: 0.86rem;
    margin: 0.3rem 0 0;
}

.file-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.65rem;
    background: __PANEL__;
    border: 1px solid __BORDER__;
    border-radius: 0.7rem;
    padding: 0.55rem 0.8rem;
    margin-top: 0.8rem;
}
.file-chip-icon {
    background: rgba(59,130,246,0.12);
    border-radius: 0.5rem;
    padding: 0.28rem;
    font-size: 1rem;
}
.file-chip-name {
    font-size: 0.84rem;
    font-weight: 600;
    color: __TEXT__;
}
.file-chip-size {
    font-size: 0.7rem;
    color: __SUBTEXT__;
}
.file-chip-check {
    width: 1.2rem;
    height: 1.2rem;
    background: #DCFCE7;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #15803D;
    font-size: 0.68rem;
    font-weight: 700;
}

.qa-card-label {
    display: flex;
    align-items: center;
    border-left: 4px solid #3B82F6;
    padding-left: 0.7rem;
    margin: 1rem 0 0.9rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: __TEXT__;
}
.answer-card {
    background: __PANEL__;
    border: 1px solid __BORDER__;
    border-radius: 0.9rem;
    padding: 1.3rem;
    position: relative;
    margin-top: 1rem;
}
.answer-badge {
    position: absolute;
    top: -0.7rem;
    left: 1rem;
    background: #8B7A68;
    color: #fff;
    padding: 0.16rem 0.68rem;
    border-radius: 9999px;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.answer-text {
    font-size: 0.95rem;
    line-height: 1.65;
    color: __TEXT__;
    margin: 0.5rem 0 0.8rem;
}
.answer-source {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding-top: 0.7rem;
    border-top: 1px solid __BORDER__;
    font-size: 0.74rem;
    font-weight: 600;
    color: __SUBTEXT__;
}

.chat-history-title {
    margin-top: 1.2rem;
    margin-bottom: 0.7rem;
    font-size: 0.8rem;
    font-weight: 700;
    color: __SUBTEXT__;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.chat-history-row {
    margin-top: 0.45rem;
    padding: 0.6rem 0.75rem;
    border: 1px solid __BORDER__;
    border-radius: 0.65rem;
    background: __PANEL__;
    font-size: 0.9rem;
    color: __TEXT__;
}

.chat-history-answer {
    margin: 0.45rem 0 0.6rem;
    padding: 0.7rem 0.85rem;
    border: 1px solid __BORDER__;
    border-radius: 0.65rem;
    background: __PANEL__;
}

.chat-history-answer-text {
    font-size: 0.9rem;
    line-height: 1.6;
    color: __TEXT__;
}

.chat-history-answer-source {
    margin-top: 0.45rem;
    font-size: 0.74rem;
    color: __SUBTEXT__;
}

div[data-testid="stFileUploader"] > label {
    display: none;
}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
    border: 1px dashed __BORDER__ !important;
    background: __PANEL__ !important;
    border-radius: 0.75rem !important;
    padding: 1.5rem 1rem !important;
    min-height: 140px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0.8rem !important;
    transition: background 0.2s ease, border-color 0.2s ease !important;
}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover {
    border-color: __SUBTEXT__ !important;
}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] {
    order: 1 !important;
    margin: 0 !important;
    font-size: 0 !important;
    color: transparent !important;
    text-align: center !important;
}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"]::before {
    content: "Drag and drop file here";
    display: block;
    font-size: 0.92rem;
    font-weight: 700;
    color: __TEXT__;
    line-height: 1.35;
}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] small {
    display: none !important;
}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button {
    order: 2 !important;
    border-radius: 0.55rem !important;
    border: 1px solid __BORDER__ !important;
    background: __PANEL__ !important;
    color: __TEXT__ !important;
    font-weight: 700 !important;
    padding: 0.45rem 0.9rem !important;
}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button:hover {
    background: __PANEL__ !important;
    border-color: __SUBTEXT__ !important;
}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button > div {
    font-size: 0 !important;
}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button > div::after {
    content: "Chon file PDF";
    font-size: 0.9rem;
}

div[data-testid="stTextInput"] > div > div > input {
    border-radius: 0.75rem !important;
    padding: 0.9rem 1rem !important;
    background: __INPUT_BG__ !important;
    border: 1px solid __BORDER__ !important;
    font-size: 0.9375rem !important;
    color: __TEXT__ !important;
}
div[data-testid="stTextInput"] > div > div > input::placeholder {
    color: __INPUT_PLACEHOLDER__ !important;
    opacity: 0.8 !important;
}
div[data-testid="stTextInput"] > div > div > input:focus {
    box-shadow: 0 0 0 2px rgba(139,122,104,0.35) !important;
}
.stButton > button {
    border-radius: 0.55rem !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    color: __TEXT__ !important;
    box-shadow: none !important;
}

.stButton > button:hover {
    background: transparent !important;
    border-color: __BORDER__ !important;
}

.stButton > button[kind="tertiary"] {
    border: none !important;
    padding-left: 0.25rem !important;
    padding-right: 0.25rem !important;
}

.stToggle label {
    color: __TEXT__ !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}
.stToggle label span {
    color: __TEXT__ !important;
}

div[data-testid="stSidebarUserContent"] {
    padding-bottom: 1rem !important;
}

__SIDEBAR_CSS__
</style>
"""

    return (
        css.replace("__BG__", bg)
        .replace("__PANEL__", panel)
        .replace("__TEXT__", text)
        .replace("__SUBTEXT__", subtext)
        .replace("__BORDER__", border)
        .replace("__SIDEBAR_BG__", sidebar_bg)
        .replace("__INPUT_BG__", input_bg)
        .replace("__INPUT_PLACEHOLDER__", input_placeholder)
        .replace("__SIDEBAR_CSS__", sidebar_css)
    )

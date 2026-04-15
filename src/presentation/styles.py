def get_css(dark_mode: bool = False, sidebar_collapsed: bool = False) -> str:
    """Return CSS by theme and sidebar visibility."""
    bg = "#1F2329" if dark_mode else "#F8F9FA"
    panel = "#2B2F36" if dark_mode else "#FFFFFF"
    text = "#FFFFFF" if dark_mode else "#212529"
    subtext = "#B7C0CB" if dark_mode else "#6C757D"
    border = "#3A4048" if dark_mode else "#DEE2E6"
    sidebar_bg = "#2C2F33" if dark_mode else "#2C2F33"
    input_bg = "#343A40" if dark_mode else "#FFFFFF"
    input_placeholder = "#8B939D" if dark_mode else "#6C757D"
    primary = "#007BFF"
    secondary = "#FFC107"

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
section[data-testid="stSidebar"] button,
section[data-testid="stSidebar"] a,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] label {
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] .sidebar-panel {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 0.7rem;
    padding: 0.65rem 0.75rem;
    margin-bottom: 0.8rem;
}
section[data-testid="stSidebar"] .sidebar-panel-item {
    font-size: 0.8rem;
    line-height: 1.45;
    color: #FFFFFF !important;
    padding: 0.15rem 0;
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
    font-weight: 900;
    color: #FFFFFF !important;
    padding: 0.35rem 0.35rem 0.8rem;
}
.sidebar-section-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #FFFFFF !important;
    font-weight: 800;
    margin-top: 1.2rem;
    margin-bottom: 0.8rem;
    padding: 0 0.2rem;
}
.empty-chat-chip {
    font-size: 0.85rem;
    color: #FFFFFF !important;
    padding: 0.5rem 0.2rem;
}

section[data-testid="stSidebar"] .stCaption {
    color: #FFFFFF !important;
    font-size: 0.74rem !important;
}
section[data-testid="stSidebar"] .stCaption p {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #FFFFFF !important;
    color: #111111 !important;
    border: 1px solid #CED4DA !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] span,
section[data-testid="stSidebar"] [data-baseweb="select"] svg,
section[data-testid="stSidebar"] [data-baseweb="select"] input {
    color: #111111 !important;
    fill: #111111 !important;
}

div[role="listbox"] {
    background: #FFFFFF !important;
    color: #111111 !important;
}

div[role="listbox"] * {
    color: #111111 !important;
}

section[data-testid="stSidebar"] [data-testid="stPopover"] button {
    background: #FFFFFF !important;
    color: #111111 !important;
    border: 1px solid #CED4DA !important;
}

section[data-testid="stSidebar"] [data-testid="stPopover"] button:hover {
    background: #F1F3F5 !important;
    color: #111111 !important;
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
.quick-flow-wrap {
    margin-top: 0.62rem;
    display: flex;
    align-items: center;
    gap: 0.45rem;
    flex-wrap: wrap;
}
.quick-flow-card {
    background: #343A40;
    border: 1px solid #495057;
    color: #FFFFFF;
    border-radius: 0.55rem;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.36rem 0.58rem;
    white-space: nowrap;
}
.quick-flow-sep {
    color: __SUBTEXT__;
    font-size: 0.75rem;
    font-weight: 700;
}

.timeline-wrap {
    margin-top: 0.9rem;
    margin-bottom: 0.8rem;
    padding: 0.85rem 0.95rem;
    background: __PANEL__;
    border: 1px solid __BORDER__;
    border-radius: 0.75rem;
}
.timeline-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: __SUBTEXT__;
    margin-bottom: 0.65rem;
}
.timeline-cards {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
}
.timeline-card {
    border-radius: 0.6rem;
    padding: 0.42rem 0.7rem;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    border: 1px solid transparent;
}
.timeline-card.pending {
    background: #343A40;
    border-color: #495057;
    color: #FFFFFF;
}
.timeline-card.active {
    background: #E7F1FF;
    border-color: #A9CFF7;
    color: #1F5AA6;
}
.timeline-card.done {
    background: #FFF4D6;
    border-color: #F2D277;
    color: #7A5B00;
}
.timeline-sep {
    color: __SUBTEXT__;
    font-size: 0.78rem;
    font-weight: 700;
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
    border-left: 4px solid __PRIMARY__;
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
    background: __PRIMARY__;
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
    border: 1px solid __SECONDARY__ !important;
    background: __SECONDARY__ !important;
    color: #212529 !important;
    font-weight: 700 !important;
    padding: 0.45rem 0.9rem !important;
}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button:hover {
    background: #FFD94D !important;
    border-color: #FFD94D !important;
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
    background: __PRIMARY__ !important;
    border: 1px solid __PRIMARY__ !important;
    color: #FFFFFF !important;
    box-shadow: none !important;
}

.stButton > button:hover {
    background: #0069D9 !important;
    border-color: #0062CC !important;
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
        .replace("__PRIMARY__", primary)
        .replace("__SECONDARY__", secondary)
        .replace("__SIDEBAR_CSS__", sidebar_css)
    )

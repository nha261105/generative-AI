def get_css() -> str:
    """Trả về toàn bộ CSS custom cho ứng dụng SmartDoc AI."""
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, .font-headline {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #2C2F33 !important;
    padding: 1.5rem 1rem;
}
section[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}
section[data-testid="stSidebar"] .sidebar-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.25rem;
    font-weight: 900;
    color: #FFFFFF !important;
    letter-spacing: -0.025em;
    padding: 1rem 0.5rem 1.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 1.5rem;
}
.sidebar-section-label {
    font-size: 0.625rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748B !important;
    font-weight: 700;
    margin-bottom: 0.75rem;
    padding: 0 0.5rem;
}
.step-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.35rem 0.5rem;
    margin-bottom: 0.5rem;
}
.step-badge {
    width: 1.5rem; height: 1.5rem;
    display: flex; align-items: center; justify-content: center;
    border-radius: 9999px;
    background: rgba(255,255,255,0.1);
    font-size: 0.625rem; font-weight: 700;
    flex-shrink: 0;
    color: #CBD5E1 !important;
}
.step-badge.active {
    background: #0059BB;
    color: #FFFFFF !important;
}
.step-text { font-size: 0.875rem; }
.step-text.active { color: #FFFFFF !important; font-weight: 600; }

.nav-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border-radius: 0.75rem;
    margin-bottom: 0.25rem;
    font-size: 0.875rem;
    cursor: pointer;
    transition: background 0.15s;
    text-decoration: none;
}
.nav-item.active {
    background: rgba(255,255,255,0.1);
    color: #FFFFFF !important;
    font-weight: 600;
}
.nav-item:not(.active) { color: #94A3B8 !important; }
.nav-item:hover:not(.active) { background: rgba(255,255,255,0.05); color: #FFFFFF !important; }

.config-chip {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: rgba(255,255,255,0.05);
    border-radius: 0.5rem;
    margin-bottom: 0.4rem;
    font-size: 0.6875rem;
    font-weight: 500;
    color: #CBD5E1 !important;
}
.sidebar-footer {
    border-top: 1px solid rgba(255,255,255,0.05);
    padding-top: 1rem;
    margin-top: auto;
}

/* ── Main header ── */
.main-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.5rem 0 2rem;
    border-bottom: 1px solid #E7E8E9;
    margin-bottom: 2rem;
}
.main-header h1 {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.75rem; font-weight: 900;
    color: #191C1D; line-height: 1;
    margin: 0;
}
.main-header p { color: #414754; font-size: 0.875rem; margin: 0.25rem 0 0; }
.avatar {
    width: 2.5rem; height: 2.5rem;
    background: #0070EA;
    border-radius: 9999px;
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-weight: 700; font-size: 0.875rem;
}

/* ── Upload zone ── */
.upload-card {
    background: #FFFFFF;
    border-radius: 1rem;
    padding: 2rem;
    box-shadow: 0 8px 30px rgba(0,0,0,0.04);
    margin-bottom: 1.5rem;
}
.upload-dropzone {
    border: 2px dashed #FDC003;
    background: rgba(253,192,3,0.03);
    border-radius: 0.75rem;
    padding: 3rem 2rem;
    text-align: center;
    transition: background 0.2s;
}
.upload-dropzone:hover { background: rgba(253,192,3,0.07); }
.upload-icon-wrap {
    width: 4rem; height: 4rem;
    background: #FFDF9E;
    border-radius: 9999px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 1rem;
    font-size: 2rem;
}
.upload-dropzone h3 {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.125rem; font-weight: 700;
    color: #191C1D; margin: 0 0 0.25rem;
}
.upload-dropzone p { color: #414754; font-size: 0.875rem; margin: 0 0 1.5rem; }

/* ── File chip ── */
.file-chip {
    display: inline-flex; align-items: center; gap: 0.75rem;
    background: #EDEEEF;
    border-radius: 0.75rem;
    padding: 0.75rem 1rem;
    margin-top: 1.25rem;
}
.file-chip-icon {
    background: #fff;
    border-radius: 0.5rem;
    padding: 0.4rem;
    font-size: 1.25rem;
}
.file-chip-name { font-size: 0.875rem; font-weight: 600; color: #191C1D; }
.file-chip-size { font-size: 0.6875rem; color: #414754; }
.file-chip-check {
    width: 1.5rem; height: 1.5rem;
    background: #DCFCE7;
    border-radius: 9999px;
    display: flex; align-items: center; justify-content: center;
    color: #15803D; font-size: 0.75rem; font-weight: 700;
}

/* ── Progress pipeline ── */
.pipeline-card { margin-bottom: 1.5rem; }
.pipeline-label {
    display: flex; justify-content: space-between; align-items: flex-end;
    margin-bottom: 0.5rem;
}
.pipeline-label span:first-child {
    font-size: 0.75rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.05em;
    color: #414754;
}
.pipeline-label span:last-child {
    font-size: 0.75rem; font-weight: 600; color: #0059BB;
}
.pipeline-bar-bg {
    background: #E1E3E4; border-radius: 9999px;
    height: 0.5rem; overflow: hidden; margin-bottom: 1rem;
}
.pipeline-bar-fill {
    background: #0059BB; height: 100%;
    border-radius: 9999px;
    transition: width 1s ease;
}
.pipeline-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.pipeline-step {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 1rem; border-radius: 0.75rem;
    background: #FFFFFF;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.pipeline-step.active {
    background: rgba(0,89,187,0.04);
    border: 1px solid rgba(0,89,187,0.15);
}
.pipeline-step.pending { opacity: 0.5; }
.pipeline-step span.label { font-size: 0.875rem; font-weight: 500; color: #191C1D; }
.pipeline-step.active span.label { font-weight: 700; color: #0059BB; }
.pipeline-step.pending span.label { color: #414754; }
.spinner {
    width: 1rem; height: 1rem;
    border: 2px solid #0059BB;
    border-top-color: transparent;
    border-radius: 9999px;
    animation: spin 0.7s linear infinite;
    flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Q&A ── */
.qa-card {
    background: #FFFFFF;
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 8px 30px rgba(0,0,0,0.04);
    margin-bottom: 1.5rem;
}
.qa-card-label {
    display: flex; align-items: center;
    border-left: 4px solid #0059BB;
    padding-left: 0.75rem;
    margin-bottom: 1rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.875rem; font-weight: 700;
    color: #191C1D;
}
.answer-card {
    background: rgba(216,226,255,0.3);
    border: 1px solid rgba(0,89,187,0.1);
    border-radius: 1rem;
    padding: 2rem;
    position: relative;
    margin-top: 1rem;
}
.answer-badge {
    position: absolute; top: -0.875rem; left: 1.5rem;
    background: #0059BB; color: #fff;
    padding: 0.2rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.65rem; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase;
    display: flex; align-items: center; gap: 0.4rem;
    box-shadow: 0 4px 12px rgba(0,89,187,0.35);
}
.answer-text {
    font-size: 1rem; line-height: 1.7;
    color: #191C1D; margin: 0.5rem 0 1rem;
}
.answer-source {
    display: flex; align-items: center; gap: 0.5rem;
    padding-top: 0.875rem;
    border-top: 1px solid rgba(0,89,187,0.1);
    font-size: 0.75rem; font-weight: 600; color: #414754;
}
.action-buttons { display: flex; gap: 0.5rem; margin-top: 1rem; }
.action-btn {
    padding: 0.4rem 0.75rem;
    border-radius: 0.5rem;
    background: rgba(255,255,255,0.7);
    border: 1px solid rgba(0,0,0,0.06);
    cursor: pointer; font-size: 0.8rem;
    color: #414754; transition: background 0.15s;
}
.action-btn:hover { background: rgba(255,255,255,1); }

/* ── Status FAB ── */
.status-fab {
    display: inline-flex; align-items: center; gap: 0.75rem;
    background: rgba(255,255,255,0.9);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(193,198,215,0.4);
    border-radius: 1rem;
    padding: 0.875rem 1.25rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
    font-size: 0.75rem; font-weight: 700;
    color: #414754;
    font-family: 'Plus Jakarta Sans', sans-serif;
    margin-top: 1rem;
}
.pulse-dot {
    width: 0.5rem; height: 0.5rem;
    background: #22C55E; border-radius: 9999px;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(1.3); }
}

/* ── Streamlit widget overrides ── */
div[data-testid="stFileUploader"] > label { display: none; }
div[data-testid="stFileUploader"] section {
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
}
div[data-testid="stTextInput"] > div > div > input {
    border-radius: 0.75rem !important;
    padding: 1rem 1.25rem !important;
    background: #F3F4F5 !important;
    border: none !important;
    font-size: 0.9375rem !important;
}
div[data-testid="stTextInput"] > div > div > input:focus {
    box-shadow: 0 0 0 2px rgba(0,89,187,0.2) !important;
}
.stButton > button {
    border-radius: 0.5rem !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
}
</style>
"""
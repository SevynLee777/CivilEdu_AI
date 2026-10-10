import streamlit as st
import importlib
import unit_manager
import logger_utils
import data_loader
import os
import io
import json
import html
import re
import random
import copy
from dotenv import load_dotenv

# 強制重載自訂模組，徹底解決 Streamlit Cloud 熱重載時使用舊模組快取問題
try:
    importlib.reload(unit_manager)
except Exception:
    pass

def safe_extract_text_from_file_upload(file_input, filename=""):
    """安全解析上傳檔案文字，優先呼叫 unit_manager，若遇模組快取延遲則以本地備援執行"""
    if hasattr(unit_manager, 'extract_text_from_file_upload'):
        try:
            return unit_manager.extract_text_from_file_upload(file_input, filename)
        except Exception as e:
            print(f"[Warning] unit_manager.extract_text_from_file_upload 調用異常: {e}")

    # 本地備援實作 (相容 Streamlit UploadedFile 與 BytesIO)
    if hasattr(file_input, 'name') and not filename:
        filename = file_input.name
    if hasattr(file_input, 'seek'):
        try: file_input.seek(0)
        except Exception: pass
    if hasattr(file_input, 'read'):
        file_bytes = file_input.read()
    elif isinstance(file_input, bytes):
        file_bytes = file_input
    else:
        file_bytes = bytes(file_input)
    if hasattr(file_input, 'seek'):
        try: file_input.seek(0)
        except Exception: pass

    base_name = re.sub(r'\.[^.]+$', '', filename).strip() if filename else "新學習單元"
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    extracted_text = ""
    try:
        if ext == 'docx':
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            extracted_text = '\n'.join([p.text.strip() for p in doc.paragraphs if p.text.strip()])
        elif ext == 'pdf':
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages_text = [page.extract_text().strip() for page in pdf.pages if page.extract_text()]
                extracted_text = '\n\n'.join(pages_text)
        elif ext in ['txt', 'md']:
            try:
                extracted_text = file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                extracted_text = file_bytes.decode('cp950', errors='ignore')
        else:
            try:
                extracted_text = file_bytes.decode('utf-8')
            except Exception:
                extracted_text = file_bytes.decode('cp950', errors='ignore')
    except Exception as e:
        print(f"[Warning] 本地檔案解析異常: {e}")
        try:
            extracted_text = file_bytes.decode('utf-8', errors='ignore')
        except Exception:
            extracted_text = ""
    return base_name, extracted_text.strip()

def safe_randomize_practice_questions(unit, num_questions=8):
    """安全抽取練習題目與洗牌選項，優先呼叫 unit_manager，若遇模組快取延遲則以本地備援執行"""
    if hasattr(unit_manager, 'randomize_practice_questions'):
        try:
            return unit_manager.randomize_practice_questions(unit, num_questions)
        except Exception as e:
            print(f"[Warning] unit_manager.randomize_practice_questions 調用異常: {e}")

    # 本地備援實作
    raw_qs = unit.get("practice_questions", [])
    if not raw_qs:
        return []
    sample_size = min(num_questions, len(raw_qs))
    selected_qs = random.sample(raw_qs, sample_size)
    random.shuffle(selected_qs)
    processed_qs = []
    for q in selected_qs:
        q_copy = copy.deepcopy(q)
        original_options = q_copy.get("options", [])
        orig_corr_idx = q_copy.get("correct_index", 0)
        clean_options = [re.sub(r'^[A-Da-d]\s*[\)\.\、\:\-]?\s*', '', str(opt)).strip() for opt in original_options]
        correct_content = clean_options[orig_corr_idx] if 0 <= orig_corr_idx < len(clean_options) else (clean_options[0] if clean_options else "")
        random.shuffle(clean_options)
        new_options = [f"{chr(65 + idx)}) {opt_text}" for idx, opt_text in enumerate(clean_options)]
        new_corr_idx = clean_options.index(correct_content) if correct_content in clean_options else 0
        q_copy["options"] = new_options
        q_copy["correct_index"] = new_corr_idx
        processed_qs.append(q_copy)
    return processed_qs

# --- Page Config ---
st.set_page_config(
    page_title="國中公民思辨星系 ｜ AI 智慧自主學習館",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_dotenv()
TEACHER_PASSWORD = os.getenv("TEACHER_PASSWORD", "MCJH2026")

# --- GSAT Exam Galaxy Inspired Celestial Theme ---
st.markdown("""
<style>
    /* Google Fonts: Noto Serif TC (思源宋體) + Noto Sans TC (思源黑體) */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@600;700;900&family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    :root {
        --galaxy-bg: #060b16;
        --galaxy-ink: #0a1526;
        --galaxy-ink-card: #0d1c33;
        --galaxy-paper: #d0e0ee;
        --galaxy-paper-muted: #9bb7d4;
        --galaxy-gold: #5b9ed7;
        --galaxy-gold-pale: #b2d7fc;
        --galaxy-amber: #f4d38b;
        --galaxy-line: rgba(150, 192, 230, 0.22);
        --font-serif: 'Noto Serif TC', serif;
        --font-sans: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

        /* 全載具自適應流體字級變數：依螢幕尺寸自動縮放，設定保底清晰字級，避免字體過小 */
        --fluid-base: clamp(15.5px, 0.4vw + 14.5px, 17.5px);
        --fluid-h1: clamp(1.75rem, 1.8vw + 1.25rem, 2.35rem);
        --fluid-h2: clamp(1.45rem, 1.3vw + 1.1rem, 1.95rem);
        --fluid-h3: clamp(1.22rem, 0.9vw + 0.95rem, 1.55rem);
        --fluid-h4: clamp(1.1rem, 0.6vw + 0.95rem, 1.35rem);
        --fluid-body: clamp(1.02rem, 0.35vw + 0.96rem, 1.16rem);
        --fluid-sub: clamp(0.95rem, 0.25vw + 0.9rem, 1.05rem);
    }
    
    html, body {
        font-size: var(--fluid-base) !important;
        font-family: var(--font-sans);
    }
    
    /* 墨染深邃背景 + 水墨柔光光暈 */
    .stApp {
        font-size: 1rem !important;
        background-color: var(--galaxy-bg) !important;
        background-image: 
            radial-gradient(circle at 68% -12%, #274a73 0, transparent 38rem),
            radial-gradient(circle at 12% 108%, #16345c 0, transparent 42rem),
            linear-gradient(165deg, #0d1c33 0%, #0a1526 45%, #060b16 100%) !important;
        color: var(--galaxy-paper) !important;
    }
    
    .stMarkdown p, .stMarkdown span, .stMarkdown strong, .stMarkdown li, .stMarkdown div {
        color: var(--galaxy-paper) !important;
        font-size: var(--fluid-body) !important;
        line-height: 1.8 !important;
    }

    /* 全域文字、選項、按鈕與輸入框流體字級統一防護 */
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span,
    div[data-testid="stCheckbox"] label p,
    div[data-testid="stCheckbox"] label span {
        font-size: var(--fluid-body) !important;
        color: #e2e8f0 !important;
        line-height: 1.6 !important;
    }

    input, textarea, .stTextInput input, .stTextArea textarea {
        font-size: var(--fluid-body) !important;
        color: #ffffff !important;
    }

    label p, label span, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span {
        font-size: var(--fluid-sub) !important;
        font-weight: 600 !important;
        color: #cbd5e1 !important;
    }

    [data-testid="stCaptionContainer"] p, .stCaption {
        font-size: var(--fluid-sub) !important;
        color: var(--galaxy-paper-muted) !important;
        line-height: 1.6 !important;
    }

    div[data-baseweb="select"] div, div[data-testid="stSelectbox"] div {
        font-size: var(--fluid-body) !important;
        color: #ffffff !important;
    }

    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"],
    .stButton button {
        font-size: var(--fluid-body) !important;
        font-weight: 600 !important;
    }

    div[data-testid="stAlert"] div, div[data-testid="stAlert"] p {
        font-size: var(--fluid-body) !important;
        line-height: 1.65 !important;
    }

    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary p {
        font-size: var(--fluid-body) !important;
        font-weight: 600 !important;
    }
    
    h1, .app-title {
        font-family: var(--font-serif) !important;
        color: #ffffff !important;
        font-size: var(--fluid-h1) !important;
        line-height: 1.3 !important;
        letter-spacing: -0.015em;
    }

    h2 {
        font-family: var(--font-serif) !important;
        color: #ffffff !important;
        font-size: var(--fluid-h2) !important;
        line-height: 1.35 !important;
    }

    h3 {
        font-family: var(--font-serif) !important;
        color: #95c6f4 !important;
        font-size: var(--fluid-h3) !important;
        line-height: 1.4 !important;
    }

    h4 {
        font-family: var(--font-serif) !important;
        color: #95c6f4 !important;
        font-size: var(--fluid-h4) !important;
        line-height: 1.4 !important;
    }

    /* 眉標（Eyebrow）與狀態膠囊：提升可讀性與對比度 */
    .eyebrow {
        font-size: var(--fluid-sub) !important;
        font-weight: 700 !important;
        color: var(--galaxy-gold-pale) !important;
        letter-spacing: 0.16em !important;
        text-transform: uppercase;
        margin: 0 0 0.4rem 0;
    }

    /* 頂部銀河 Header */
    .galaxy-header {
        position: relative;
        background: rgba(13, 28, 51, 0.68);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--galaxy-line);
        border-radius: 18px;
        padding: 1.6rem 2.2rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45);
    }

    /* 品牌印章 */
    .brand-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.7rem;
        height: 2.7rem;
        background: #2c5a92;
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.28);
        font-family: var(--font-serif);
        font-size: 1.35rem;
        font-weight: 700;
        border-radius: 7px;
        box-shadow: 0 0 1.5rem rgba(50, 110, 166, 0.45);
        flex-shrink: 0;
    }

    /* 呼吸燈狀態膠囊 */
    .pulse-status {
        display: inline-flex;
        align-items: center;
        gap: 0.6rem;
        background: rgba(208, 224, 238, 0.08);
        border: 1px solid rgba(208, 224, 238, 0.25);
        border-radius: 999px;
        padding: 0.48rem 1.15rem;
        font-size: var(--fluid-sub) !important;
        color: var(--galaxy-paper);
        font-weight: 500;
        letter-spacing: 0.05em;
    }

    .pulse-dot {
        width: 0.45rem;
        height: 0.45rem;
        background: var(--galaxy-amber);
        border-radius: 50%;
        box-shadow: 0 0 8px var(--galaxy-amber);
        animation: pulseGlow 2s infinite ease-in-out;
    }

    @keyframes pulseGlow {
        0%, 100% { opacity: 0.35; transform: scale(0.9); }
        50% { opacity: 1; transform: scale(1.25); box-shadow: 0 0 12px var(--galaxy-amber); }
    }

    /* 01, 02 序號風格重點手札卡片 */
    .numbered-card {
        position: relative;
        background: rgba(14, 29, 51, 0.72);
        border: 1px solid var(--galaxy-line);
        border-radius: 14px;
        padding: 1.3rem 1.6rem 1.3rem 4.4rem;
        margin-bottom: 0.95rem;
        transition: all 0.25s ease;
    }

    .numbered-card:hover {
        border-color: rgba(149, 198, 244, 0.45);
        background: rgba(20, 39, 67, 0.85);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }

    .numbered-card .card-idx {
        position: absolute;
        top: 1.15rem;
        left: 1.35rem;
        font-family: var(--font-serif);
        font-size: 1.55rem;
        font-weight: 900;
        color: var(--galaxy-gold-pale);
        opacity: 0.75;
        line-height: 1;
    }

    /* Cards */
    .feature-card {
        background: rgba(14, 29, 51, 0.75);
        border: 1px solid var(--galaxy-line);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }

    .key-point-card {
        background: rgba(12, 24, 43, 0.75);
        border-left: 4px solid var(--galaxy-gold);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        font-size: 1.05rem;
        line-height: 1.6;
    }

    .case-card {
        background: linear-gradient(135deg, rgba(14, 29, 51, 0.9) 0%, rgba(26, 48, 80, 0.75) 100%);
        border: 1px solid rgba(91, 158, 215, 0.35);
        border-radius: 16px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }

    .remedial-box {
        background: linear-gradient(135deg, rgba(166, 69, 50, 0.15) 0%, rgba(14, 29, 51, 0.9) 100%);
        border: 1.5px solid rgba(244, 211, 139, 0.5);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.2rem 0;
    }

    /* 星系觀測站 (Observatory Strip) 數據橫幅 */
    .observatory-strip {
        background: rgba(13, 25, 43, 0.85);
        border: 1px solid var(--galaxy-line);
        border-radius: 16px;
        padding: 1.4rem 1.8rem;
        display: flex;
        justify-content: space-around;
        align-items: center;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }

    .observatory-strip strong {
        display: block;
        font-family: var(--font-serif);
        font-size: 2.1rem;
        color: var(--galaxy-amber);
        letter-spacing: -0.02em;
    }

    .observatory-strip span {
        font-size: var(--fluid-sub) !important;
        color: var(--galaxy-paper-muted);
        letter-spacing: 0.1em;
    }

    .summary-metric-card {
        background: rgba(14, 29, 51, 0.85);
        border: 1px solid var(--galaxy-line);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    }

    /* ══════════════════════════════════════════════════════════════════════
       標籤頁（Tabs）經典樣式 — 保留純粹標籤頁導航質感，加大清晰字級
       ══════════════════════════════════════════════════════════════════════ */
    div[data-testid="stTabs"] {
        background-color: transparent !important;
        border-bottom: 1.5px solid var(--galaxy-line) !important;
        margin-bottom: 1.6rem !important;
    }

    div[data-testid="stTabs"] [role="tablist"],
    div[data-testid="stTabs"] div[data-baseweb="tab-list"],
    div[data-testid="stTabs"] .react-aria-TabList {
        gap: 0.5rem !important;
        border: none !important;
    }

    /* 頁籤本體（經典膠囊標籤頁樣式） */
    div[data-testid="stTabs"] [data-testid="stTab"],
    div[data-testid="stTabs"] [role="tab"],
    div[data-testid="stTabs"] .react-aria-Tab,
    div[data-testid="stTabs"] button,
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 999px !important;
        margin-right: 6px !important;
        padding: 0.62rem 1.45rem !important;
        height: auto !important;
        min-height: 44px !important;
        transition: all 0.25s ease !important;
        cursor: pointer !important;
    }

    div[data-testid="stTabs"] [data-testid="stTab"]:hover,
    div[data-testid="stTabs"] [role="tab"]:hover,
    div[data-testid="stTabs"] .react-aria-Tab:hover,
    div[data-testid="stTabs"] button:hover {
        background: rgba(208, 224, 238, 0.08) !important;
        border-color: rgba(150, 192, 230, 0.3) !important;
    }

    /* 頁籤文字：加大字級，清晰舒適 */
    div[data-testid="stTabs"] [data-testid="stTab"],
    div[data-testid="stTabs"] [data-testid="stTab"] *,
    div[data-testid="stTabs"] [role="tab"],
    div[data-testid="stTabs"] [role="tab"] *,
    div[data-testid="stTabs"] .react-aria-Tab,
    div[data-testid="stTabs"] .react-aria-Tab *,
    div[data-testid="stTabs"] button p,
    div[data-testid="stTabs"] button span,
    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] span {
        color: var(--galaxy-paper-muted) !important;
        font-family: var(--font-sans) !important;
        font-size: clamp(1.18rem, 0.35vw + 1.12rem, 1.32rem) !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        line-height: 1.4 !important;
    }

    /* 選中標籤頁（經典金黃下標線與微柔光底色） */
    div[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"],
    div[data-testid="stTabs"] [data-testid="stTab"][data-selected="true"],
    div[data-testid="stTabs"] [data-testid="stTab"][data-selected],
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"],
    div[data-testid="stTabs"] [role="tab"][data-selected],
    div[data-testid="stTabs"] .react-aria-Tab[data-selected],
    div[data-testid="stTabs"] button[aria-selected="true"],
    button[data-baseweb="tab"][aria-selected="true"] {
        background: rgba(208, 224, 238, 0.1) !important;
        border: 1px solid var(--galaxy-line) !important;
        border-bottom: 3px solid var(--galaxy-amber) !important;
    }

    div[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] *,
    div[data-testid="stTabs"] [data-testid="stTab"][data-selected="true"] *,
    div[data-testid="stTabs"] [data-testid="stTab"][data-selected] *,
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] *,
    div[data-testid="stTabs"] [role="tab"][data-selected] *,
    div[data-testid="stTabs"] .react-aria-Tab[data-selected] *,
    div[data-testid="stTabs"] button[aria-selected="true"] *,
    button[data-baseweb="tab"][aria-selected="true"] * {
        color: var(--galaxy-amber) !important;
        font-weight: 700 !important;
    }

    /* 隱藏原生底線指示器，由標籤頁專屬下邊框呈現 */
    div[data-testid="stTabs"] .react-aria-SelectionIndicator,
    div[data-testid="stTabs"] div[data-baseweb="tab-highlight"],
    div[data-testid="stTabs"] div[data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Badges */
    .badge-status-mastered {
        background: rgba(82, 125, 113, 0.25);
        border: 1.5px solid #527d71;
        color: #93c5fd !important;
        padding: 5px 13px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }

    .badge-status-practice {
        background: rgba(244, 211, 139, 0.18);
        border: 1.5px solid #f4d38b;
        color: #fde047 !important;
        padding: 5px 13px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }

    .badge-status-look {
        background: rgba(166, 69, 50, 0.22);
        border: 1.5px solid #a64532;
        color: #fca5a5 !important;
        padding: 5px 13px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }

    .reader-container {
        background-color: #070e1a !important;
        color: #d0e0ee !important;
        padding: 1.8rem;
        border-radius: 12px;
        border: 1px solid var(--galaxy-line);
        font-size: 1.05rem;
        line-height: 1.85;
        max-height: 450px;
        overflow-y: auto;
        white-space: pre-wrap;
    }

    /* 核心觀念直式心智圖外框卡片與放大優化 */
    .mindmap-card {
        background: rgba(11, 23, 42, 0.88);
        border: 1px solid rgba(149, 198, 244, 0.32);
        border-radius: 18px;
        padding: 1.8rem 1.4rem;
        margin: 1.2rem 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
        overflow-x: auto;
    }

    /* 直式心智圖 SVG 尺寸優化：自適應寬度，直向展開不擠壓 */
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"],
    div[data-testid="stMarkdownContainer"] .mermaid svg {
        display: block !important;
        margin: 1rem auto !important;
        width: 100% !important;
        max-width: 920px !important;
        height: auto !important;
        filter: drop-shadow(0 4px 18px rgba(0, 0, 0, 0.5)) !important;
    }

    /* 大幅提升心智圖內部文字節點大小、字重與對比度 */
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] text,
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] .nodeLabel,
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] .label,
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] span {
        font-size: 20px !important;
        font-weight: 700 !important;
        line-height: 1.5 !important;
        font-family: var(--font-sans) !important;
        fill: #ffffff !important;
        color: #ffffff !important;
        letter-spacing: 0.3px !important;
    }

    /* 頂層主要核心節點（A節點）特大字體與金色醒目標示 */
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] g[id*="flowchart-A-"] text,
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] g[id*="flowchart-A-"] .nodeLabel,
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] g[id*="flowchart-A-"] span {
        font-size: 22px !important;
        font-weight: 900 !important;
        color: #fff9e6 !important;
        fill: #fff9e6 !important;
    }

    /* 節點外框加粗與圓角提升質感 */
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] .node rect,
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] .node circle,
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] .node polygon {
        stroke-width: 2.5px !important;
        stroke: #7ab8eb !important;
        fill: #162e52 !important;
        rx: 10px !important;
        ry: 10px !important;
    }

    /* 頂層核心節點外框特別強調高亮（A節點） */
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] g[id*="flowchart-A-"] rect,
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] g[id*="flowchart-A-"] polygon {
        stroke: var(--galaxy-amber) !important;
        stroke-width: 3.5px !important;
        fill: #1f3f6d !important;
    }

    /* 箭頭與連線加粗金黃高對比 */
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] .flowchart-link,
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] path.link,
    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] .edgePath path {
        stroke: var(--galaxy-amber) !important;
        stroke-width: 2.8px !important;
    }

    div[data-testid="stMarkdownContainer"] svg[id^="mermaid-"] marker path {
        fill: var(--galaxy-amber) !important;
        stroke: var(--galaxy-amber) !important;
    }

    /* 側邊欄頂部間距緊湊化與視窗高度優化 */
    [data-testid="stSidebar"] {
        padding-top: 0 !important;
        overflow-y: auto !important;
    }
    [data-testid="stSidebar"] .block-container,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {
        padding-top: 1.2rem !important;
        padding-bottom: 4rem !important;
    }
    [data-testid="stSidebar"] h3 {
        font-size: var(--fluid-h4) !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.3rem !important;
        padding: 0 !important;
        color: #95c6f4 !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] hr {
        margin: 0.65rem 0 !important;
        border-color: rgba(150, 192, 230, 0.2) !important;
    }
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.25rem !important;
    }
    [data-testid="stSidebar"] .stRadio label p,
    [data-testid="stSidebar"] .stRadio label span {
        font-size: var(--fluid-body) !important;
        color: #e2e8f0 !important;
        line-height: 1.5 !important;
        padding-top: 1px !important;
        padding-bottom: 1px !important;
    }
    [data-testid="stSidebar"] label p,
    [data-testid="stSidebar"] label span {
        font-size: var(--fluid-sub) !important;
        font-weight: 600 !important;
        color: #cbd5e1 !important;
        margin-bottom: 0.15rem !important;
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] .stSelectbox div {
        font-size: var(--fluid-body) !important;
        color: #ffffff !important;
    }

    /* BaseWeb 下拉選單浮動層 (Popover / Menu) 視覺與高度優化 */
    div[data-baseweb="popover"] {
        z-index: 999999 !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] {
        max-height: 280px !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li,
    ul[data-testid="stSelectboxVirtualDropdown"] li span {
        padding-top: 9px !important;
        padding-bottom: 9px !important;
        min-height: 42px !important;
        font-size: var(--fluid-body) !important;
        color: #ffffff !important;
    }

    /* 載具自適應響應式斷點 (Responsive Media Queries) */
    @media (max-width: 640px) {
        :root {
            font-size: 15.5px !important;
        }
        .galaxy-header {
            padding: 1.2rem 1.4rem !important;
        }
        .numbered-card {
            padding: 1rem 1.2rem 1rem 3.6rem !important;
        }
        .card-idx {
            font-size: 1.35rem !important;
            width: 2.6rem !important;
        }
        .brand-mark {
            width: 2.3rem !important;
            height: 2.3rem !important;
            font-size: 1.2rem !important;
        }
        div[data-testid="stTabs"] [data-testid="stTab"],
        div[data-testid="stTabs"] [role="tab"],
        div[data-testid="stTabs"] .react-aria-Tab,
        div[data-testid="stTabs"] button,
        button[data-baseweb="tab"] {
            padding: 0.55rem 1.15rem !important;
            border-radius: 999px !important;
            min-height: 40px !important;
        }
        div[data-testid="stTabs"] [data-testid="stTab"] *,
        div[data-testid="stTabs"] [role="tab"] *,
        div[data-testid="stTabs"] .react-aria-Tab *,
        div[data-testid="stTabs"] button * {
            font-size: 1.12rem !important;
            font-weight: 600 !important;
        }
    }

    @media (min-width: 641px) and (max-width: 1024px) {
        :root {
            font-size: 16.5px !important;
        }
        .galaxy-header {
            padding: 1.4rem 1.8rem !important;
        }
    }

    @media (min-width: 1025px) and (max-width: 1440px) {
        :root {
            font-size: 17px !important;
        }
    }

    @media (min-width: 1441px) {
        :root {
            font-size: 17.5px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "user_role" not in st.session_state:
    st.session_state.user_role = "none"  # "none", "student", or "teacher"
if "is_teacher_authenticated" not in st.session_state:
    st.session_state.is_teacher_authenticated = False
if "role_radio_key_version" not in st.session_state:
    st.session_state.role_radio_key_version = 0
if "teacher_modal_pwd" not in st.session_state:
    st.session_state.teacher_modal_pwd = ""
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "student_class" not in st.session_state:
    st.session_state.student_class = "801"
if "student_seat" not in st.session_state:
    st.session_state.student_seat = "01"
if "current_unit_id" not in st.session_state:
    st.session_state.current_unit_id = None
if "practice_submitted" not in st.session_state:
    st.session_state.practice_submitted = False
if "practice_answers" not in st.session_state:
    st.session_state.practice_answers = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "student_tab_selection" not in st.session_state:
    st.session_state.student_tab_selection = "📖 開始學習"

def switch_to_practice_tab():
    st.session_state.student_tab_selection = "✏️ 小試身手"

def on_auth_dismiss():
    if not st.session_state.get("is_teacher_authenticated", False):
        st.session_state.user_role = "none"
        st.session_state.role_radio_key_version += 1

@st.dialog("🔒 教師身分驗證", on_dismiss=on_auth_dismiss)
def teacher_auth_dialog():
    st.markdown("切換至 **👨‍🏫 教師管理端** 需要確認教師本人身分。<br>請輸入教師管理專屬密碼：", unsafe_allow_html=True)
    with st.form("teacher_auth_modal_form", clear_on_submit=False):
        pwd = st.text_input("教師密碼", type="password", key="teacher_modal_pwd", placeholder="請輸入教師密碼")
        c1, c2 = st.columns(2)
        with c1:
            submit_btn = st.form_submit_button("🔑 確認驗證", type="primary", use_container_width=True)
        with c2:
            cancel_btn = st.form_submit_button("返回學生端", use_container_width=True)

        if submit_btn:
            if pwd == TEACHER_PASSWORD:
                st.session_state.is_teacher_authenticated = True
                st.session_state.user_role = "teacher"
                st.session_state.practice_submitted = False
                st.session_state.practice_answers = {}
                st.success("✅ 身分驗證成功！正在進入教師端...")
                st.rerun()
            else:
                st.error("❌ 密碼錯誤，請重新確認！")
        elif cancel_btn:
            on_auth_dismiss()
            st.rerun()

def format_mindmap_mermaid(raw_mermaid: str) -> str:
    if not raw_mermaid:
        return ""
    cleaned = raw_mermaid.strip()

    # 移除舊有的 %%{init: ...}%% 指令以防重複
    cleaned = re.sub(r'%%\{init:[^%]*\}%%', '', cleaned, flags=re.DOTALL).strip()

    # 將 TD / TB (由上至下橫向鋪開) 自動轉換為 LR (由左至右、直式由上而下層層展開，適配直式閱讀)
    cleaned = re.sub(r'^(graph|flowchart)\s+(TD|TB)', r'\1 LR', cleaned, flags=re.IGNORECASE | re.MULTILINE)

    # 若無流程圖宣告，預設補上 graph LR
    if not re.search(r'^(graph|flowchart)\s+', cleaned, flags=re.IGNORECASE | re.MULTILINE):
        cleaned = f"graph LR\n{cleaned}"

    init_directive = """%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#173059',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#7ab8eb',
    'lineColor': '#f4d38b',
    'secondaryColor': '#1a3668',
    'tertiaryColor': '#0b1629',
    'fontSize': '22px',
    'fontFamily': 'Noto Sans TC, -apple-system, sans-serif'
  },
  'flowchart': {
    'nodeSpacing': 35,
    'rankSpacing': 65,
    'curve': 'basis',
    'padding': 20
  }
}}%%
"""
    return f"{init_directive}{cleaned}"

# Load all units
all_units = unit_manager.load_all_units()
if not all_units:
    st.error("⚠️ 尚未載入任何學習單元，請由教師端新增教材。")
    st.stop()

# --- Sidebar: Role & Student / Navigation ---
with st.sidebar:
    st.markdown("### 🏛️ 身分切換")
    role_options = ["請選擇操作身分...", "🎓 我是學生", "👨‍🏫 我是老師"]
    cur_role_idx = 0
    if st.session_state.user_role == "student":
        cur_role_idx = 1
    elif st.session_state.user_role == "teacher":
        cur_role_idx = 2

    role_choice = st.radio(
        "選擇操作身分",
        role_options,
        index=cur_role_idx,
        key=f"role_radio_{st.session_state.role_radio_key_version}",
        label_visibility="collapsed"
    )

    if "老師" in role_choice:
        if not st.session_state.is_teacher_authenticated:
            teacher_auth_dialog()
        else:
            st.session_state.user_role = "teacher"
    elif "學生" in role_choice:
        if st.session_state.user_role != "student":
            st.session_state.user_role = "student"
            st.session_state.is_teacher_authenticated = False
            st.session_state.practice_submitted = False
            st.session_state.practice_answers = {}
            st.rerun()
    else:
        if st.session_state.user_role != "none":
            st.session_state.user_role = "none"
            st.session_state.is_teacher_authenticated = False
            st.session_state.practice_submitted = False
            st.session_state.practice_answers = {}
            st.rerun()

    st.markdown("---")

    if st.session_state.user_role == "student":
        st.markdown("### 👤 學生基本資料")
        class_options = [str(i) for i in range(801, 822)]
        seat_options = [f"{i:02d}" for i in range(1, 31)]

        col_c, col_s = st.columns(2)
        with col_c:
            selected_class = st.selectbox("班級", class_options, index=class_options.index(st.session_state.student_class) if st.session_state.student_class in class_options else 0)
        with col_s:
            selected_seat = st.selectbox("座號", seat_options, index=seat_options.index(st.session_state.student_seat) if st.session_state.student_seat in seat_options else 0)
        entered_name = st.text_input("姓名", value=st.session_state.student_name, placeholder="請輸入姓名，例如：王小明")
        
        st.session_state.student_class = selected_class
        st.session_state.student_seat = selected_seat
        st.session_state.student_name = entered_name.strip()

        st.markdown("---")
        st.markdown("### 📚 選擇學習單元")
        unit_titles = [u["title"] for u in all_units]
        unit_options = ["-- 請選擇學習單元 --"] + unit_titles
        
        cur_unit = unit_manager.get_unit(st.session_state.current_unit_id) if st.session_state.current_unit_id else None
        cur_idx = unit_options.index(cur_unit["title"]) if (cur_unit and cur_unit["title"] in unit_options) else 0
        
        selected_title = st.selectbox("選擇學習單元", unit_options, index=cur_idx, label_visibility="collapsed")
        
        # Check if changed
        if selected_title == "-- 請選擇學習單元 --":
            if st.session_state.current_unit_id is not None:
                st.session_state.current_unit_id = None
                st.session_state.practice_submitted = False
                st.session_state.practice_answers = {}
                st.session_state.chat_history = []
                st.session_state.student_tab_selection = "📖 開始學習"
                st.rerun()
        else:
            for u in all_units:
                if u["title"] == selected_title and u["id"] != st.session_state.current_unit_id:
                    st.session_state.current_unit_id = u["id"]
                    st.session_state.practice_submitted = False
                    st.session_state.practice_answers = {}
                    st.session_state.chat_history = []
                    st.session_state.student_tab_selection = "📖 開始學習"
                    st.rerun()

        # If student has filled in everything, show friendly return button
        if st.session_state.student_name.strip() and (st.session_state.current_unit_id is not None):
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 重新選定單元 / 返回導引", use_container_width=True):
                st.session_state.current_unit_id = None
                st.session_state.practice_submitted = False
                st.session_state.practice_answers = {}
                st.session_state.chat_history = []
                st.session_state.student_tab_selection = "📖 開始學習"
                st.rerun()

    elif st.session_state.user_role == "teacher":
        st.markdown("### 👨‍🏫 教師管理功能")
        st.info("教師只需新增教材與貼上課本內容，AI 自動為您萃取重點、生活案例、題目與補救指引！")
        if st.button("🔒 登出教師 / 返回首頁", use_container_width=True):
            st.session_state.user_role = "none"
            st.session_state.is_teacher_authenticated = False
            st.session_state.role_radio_key_version += 1
            st.session_state.practice_submitted = False
            st.session_state.practice_answers = {}
            st.session_state.student_tab_selection = "📖 開始學習"
            st.rerun()
    else:
        st.info("👈 請先於上方選擇您的身分（我是學生 或 我是老師）以開啟功能。")

# ══════════════════════════════════════════════
# 🏛️ 主畫面渲染路由 (Main Content Routing)
# ══════════════════════════════════════════════
is_student_ready = (
    st.session_state.user_role == "student"
    and bool(st.session_state.student_name.strip())
    and (st.session_state.current_unit_id is not None)
)
is_teacher_ready = (
    st.session_state.user_role == "teacher"
    and st.session_state.get("is_teacher_authenticated", False)
)

if is_student_ready:
    student_info = {
        "class_name": st.session_state.student_class,
        "seat_num": st.session_state.student_seat,
        "name": st.session_state.student_name or "同學"
    }

    current_unit = unit_manager.get_unit(st.session_state.current_unit_id) or all_units[0]

    # Top Galaxy Banner
    st.markdown(f"""
    <div class="galaxy-header">
        <p class="eyebrow">NATIONAL JUNIOR HIGH CIVICS AI LEARNING GALAXY</p>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div style="display: flex; align-items: center;">
                <span class="brand-mark">民</span>
                <div>
                    <h1 style="margin: 0; font-size: var(--fluid-h1); font-weight: 700; line-height: 1.2;">國中公民思辨星系</h1>
                    <p style="margin: 0.2rem 0 0 0; font-size: var(--fluid-sub); color: #8ba5be; letter-spacing: 0.05em;">歷屆觀念導引・法政思辨啟蒙・AI 助教陪伴自主成長</p>
                </div>
            </div>
            <div class="pulse-status">
                <span class="pulse-dot"></span>
                <span>星軌運行中 ｜ 👤 {student_info['class_name']} 班 {student_info['seat_num']} 號 {student_info['name']}</span>
            </div>
        </div>
        <div style="margin-top: 1rem; display: flex; gap: 0.6rem; flex-wrap: wrap;">
            <span style="background: rgba(44, 90, 146, 0.35); border: 1px solid rgba(149, 198, 244, 0.35); color: #d0e0ee; padding: 4px 14px; border-radius: 999px; font-size: var(--fluid-sub); font-weight: 600;">
                📖 當前巡航單元：{current_unit['title']}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Four Student Tabs
    valid_student_tabs = [
        "📖 開始學習",
        "✏️ 小試身手",
        "💬 公民 AI 助教隨身問",
        "🌱 我的足跡"
    ]
    if st.session_state.get("student_tab_selection") not in valid_student_tabs:
        st.session_state.student_tab_selection = valid_student_tabs[0]

    tab_learn, tab_practice, tab_ai_tutor, tab_footprint = st.tabs(
        valid_student_tabs,
        key="student_tab_selection",
        on_change="rerun"
    )

    # ──────────────────────────────────────────────
    # 1. 📖 開始學習 (Learn)
    # ──────────────────────────────────────────────
    with tab_learn:
        st.markdown(f"### 📖 {current_unit['title']} — 重點與生活實例")

        # 1. 國中生白話整理（輕鬆看懂這堂課）
        easy_content = current_unit.get("easy_content", "")
        if easy_content:
            st.markdown("#### 🌟 輕鬆看懂這堂課")
            st.markdown(f'<div class="feature-card">{easy_content}</div>', unsafe_allow_html=True)

        # 2. 核心學習重點
        key_points = current_unit.get("key_points", [])
        if key_points:
            st.markdown("---")
            st.markdown("#### 📌 核心學習重點")
            for idx, pt in enumerate(key_points):
                st.markdown(f"""
                <div class="numbered-card">
                    <span class="card-idx">{idx+1:02d}</span>
                    <div style="font-size: 1.05rem; line-height: 1.7; color: #d0e0ee;">{pt}</div>
                </div>
                """, unsafe_allow_html=True)

        # 3. 核心觀念心智圖（直式放大清晰版）
        mindmap_mermaid = current_unit.get("mindmap_mermaid", "")
        if mindmap_mermaid:
            st.markdown("---")
            st.markdown("#### 🧠 核心觀念心智圖")
            formatted_mindmap = format_mindmap_mermaid(mindmap_mermaid)
            st.markdown(f"```mermaid\n{formatted_mindmap}\n```")

        # 4. 生活與校園情境案例
        life_cases = current_unit.get("life_cases", [])
        if life_cases:
            st.markdown("---")
            st.markdown(f"#### 🏫 生活與校園情境案例 (共 {len(life_cases)} 則實例)")
            for c in life_cases:
                st.markdown(f"""
                <div class="case-card">
                    <p class="eyebrow" style="margin-bottom: 0.3rem;">CASE STUDY</p>
                    <h4 style="color: #95c6f4; margin: 0 0 0.6rem 0; font-family: var(--font-serif); font-size: var(--fluid-h4);">{c.get('title','情境實例')}</h4>
                    <p style="font-size: var(--fluid-body); line-height: 1.75; color: #d0e0ee;">{c.get('story','')}</p>
                    <div style="background: rgba(10, 21, 38, 0.85); padding: 0.9rem 1.2rem; border-radius: 10px; font-weight: 700; color: #f4d38b; border-left: 4px solid #f4d38b; margin-top: 0.8rem; font-size: var(--fluid-body);">
                        💡 思辨焦點：{c.get('takeaway','')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # 課本原文閱讀 (可摺疊)
        raw_text = current_unit.get("raw_content", "")
        if raw_text:
            with st.expander("📜 查看課本講義原文對照 (點擊展開/收合)"):
                safe_html = html.escape(raw_text)
                st.markdown(f'<div class="reader-container">{safe_html}</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="background: rgba(22, 46, 82, 0.7); border: 1px solid rgba(149, 198, 244, 0.35); border-radius: 14px; padding: 1.2rem 1.4rem; margin: 1.8rem 0 0.8rem 0; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.8rem;">
                <div style="display: flex; align-items: center; gap: 0.8rem; font-size: 1.05rem; color: #d0e0ee; line-height: 1.6;">
                    <span style="font-size: 1.5rem;">💡</span>
                    <span>讀完重點與生活案例了嗎？點擊下方按鈕即可快速切換至 <b>【✏️ 小試身手】</b> 進行觀念練習！</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.button(
            "🚀 前往【✏️ 小試身手】觀念練習",
            type="primary",
            use_container_width=True,
            key="btn_quick_jump_practice",
            on_click=switch_to_practice_tab
        )

    # ──────────────────────────────────────────────
    # 2. ✏️ 小試身手 (Practice)
    # ──────────────────────────────────────────────
    with tab_practice:
        st.markdown(f"### ✏️ 小試身手 — {current_unit['title']}")
        unit_id = current_unit.get("id", "default")
        qs_key = f"active_practice_qs_{unit_id}"
        round_key = f"practice_round_{unit_id}"

        # 若尚未隨機選題或為空，則由題庫池隨機抽取 8 題，並洗牌題序與選項
        if qs_key not in st.session_state or not st.session_state[qs_key]:
            st.session_state[qs_key] = safe_randomize_practice_questions(current_unit, num_questions=8)
            st.session_state[round_key] = st.session_state.get(round_key, 0) + 1

        questions = st.session_state[qs_key]
        current_round = st.session_state.get(round_key, 1)
        remedy_guides = current_unit.get("remediation_guides", {})
        total_pool_count = len(current_unit.get("practice_questions", []))

        st.caption(f"🎲 本次已為您從題庫池（共 {total_pool_count} 題）隨機精選 {len(questions)} 道生活化概念練習！題序與選項皆隨機安排，每次測驗皆為全新挑戰！")

        if not questions:
            st.info("這個單元暫無練習題，請直接閱讀重點喔！")
        else:
            with st.form("practice_form"):
                user_choices = {}
                for i, q in enumerate(questions):
                    tag = q.get("concept_tag", "核心觀念")
                    st.markdown(f"**第 {i+1} 題【{tag}】**")
                    st.markdown(f"##### {q.get('question','')}")
                    
                    user_choices[i] = st.radio(
                        f"選擇第 {i+1} 題答案",
                        q.get("options", []),
                        key=f"p_q_{unit_id}_{current_round}_{i}",
                        label_visibility="collapsed"
                    )
                    st.markdown("---")

                submit_btn = st.form_submit_button("📝 完成練習，查看我的理解狀態", type="primary")
                if submit_btn:
                    st.session_state.practice_submitted = True
                    st.session_state.practice_answers = user_choices
                    st.rerun()

            # Result Display
            if st.session_state.practice_submitted and st.session_state.practice_answers:
                user_ans = st.session_state.practice_answers
                score = 0
                total = len(questions)
                mastered_tags = []
                weak_tags = []

                for i, q in enumerate(questions):
                    choice = user_ans.get(i)
                    corr_idx = q.get("correct_index", 0)
                    correct_option = q.get("options", [])[corr_idx] if q.get("options") else ""
                    tag = q.get("concept_tag", "核心觀念")
                    
                    if choice == correct_option:
                        score += 1
                        mastered_tags.append(tag)
                    else:
                        weak_tags.append(tag)

                # Save practice log
                status = logger_utils.log_unit_practice(
                    student_info,
                    current_unit["id"],
                    current_unit["title"],
                    score,
                    total,
                    mastered_tags,
                    weak_tags
                )

                st.divider()
                st.markdown("### 📊 本次練習結果")

                if status == "🌳 已掌握":
                    status_html = '<span class="badge-status-mastered" style="font-size: 1.3rem;">🌳 已掌握</span>'
                    encouragement = "🎉 太優秀了！你已經完全掌握本單元的核心重點觀念！"
                elif status == "🌿 再練習":
                    status_html = '<span class="badge-status-practice" style="font-size: 1.3rem;">🌿 再練習</span>'
                    encouragement = "👍 表現不錯！大部分觀念都掌握了，參考下方貼心補充就可以更熟練囉！"
                else:
                    status_html = '<span class="badge-status-look" style="font-size: 1.3rem;">🌱 再看看</span>'
                    encouragement = "📖 沒關係！AI 老師已為你準備了超好懂的白話說明與生活案例，一起充電再出發！"

                col_res1, col_res2 = st.columns([1, 2])
                with col_res1:
                    st.markdown(f"#### 學習狀態：{status_html}", unsafe_allow_html=True)
                with col_res2:
                    st.info(encouragement)

                # ─── 智慧適性補強區 ───
                if weak_tags:
                    st.markdown("---")
                    st.markdown("#### 💡 貼心補強：AI 老師為你準備的觀念充電站")
                    st.caption("針對尚未完全理解的重點，用更簡單的白話與生活例子幫你秒懂：")

                    for w_tag in set(weak_tags):
                        guide = remedy_guides.get(w_tag, {})
                        simple_exp = guide.get("simple_explanation", "這個觀念很重要，讓我們從生活中的規律來理解它。")
                        life_case = guide.get("life_case", "就像日常遵守約定一樣。")
                        pitfall = guide.get("pitfall_tip", "記住核心關鍵，不要把兩者搞混囉！")

                        st.markdown(f"""
                        <div class="remedial-box">
                            <h4 style="color: #fb923c; margin-bottom: 0.6rem;">🎯 觀念充電：【{w_tag}】</h4>
                            <p style="font-size: 1.05rem; line-height: 1.7;"><b>💡 白話秒懂：</b>{simple_exp}</p>
                            <p style="font-size: 1.05rem; line-height: 1.7;"><b>🏫 生活比喻：</b>{life_case}</p>
                            <div style="background: rgba(15, 23, 42, 0.7); padding: 0.8rem 1.2rem; border-radius: 8px; font-weight: 700; color: #fef08a; border-left: 4px solid #f97316; margin-top: 0.8rem;">
                                📌 避坑口訣：{pitfall}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                else:
                    st.success("🌟 本單元所有重點觀念全數掌握！你可以切換到下一個單元繼續探索學習囉！")

                # Detailed Question Analysis
                st.markdown("---")
                st.markdown("#### 🔍 題目解析與對照")
                for i, q in enumerate(questions):
                    choice = user_ans.get(i)
                    corr_idx = q.get("correct_index", 0)
                    correct_option = q.get("options", [])[corr_idx] if q.get("options") else ""
                    is_correct = (choice == correct_option)

                    with st.expander(f"第 {i+1} 題 【{q.get('concept_tag','')}】 {'✅ 答對' if is_correct else '❌ 需補強'}"):
                        st.markdown(f"**題目**：{q.get('question','')}")
                        st.markdown(f"**你的選擇**：`{choice}`")
                        st.markdown(f"**正確解答**：`{correct_option}`")
                        st.markdown(f"💡 **解說**：{q.get('explanation','')}")

                if st.button("🔄 重新小試身手（隨機新題目與新選項）"):
                    st.session_state.practice_submitted = False
                    st.session_state.practice_answers = {}
                    st.session_state[round_key] = st.session_state.get(round_key, 0) + 1
                    st.session_state[qs_key] = safe_randomize_practice_questions(current_unit, num_questions=8)
                    st.rerun()

    # ──────────────────────────────────────────────
    # 3. 💬 公民 AI 助教隨身問 (AI Tutor)
    # ──────────────────────────────────────────────
    with tab_ai_tutor:
        st.markdown(f"### 💬 公民 AI 助教隨身問 — {current_unit['title']}")
        st.caption("對這堂課還有任何不懂的疑問嗎？隨時問 AI 助教，用校園日常生活幫你解惑！")

        q_user = st.text_input("輸入你的問題（例如：為什麼主權對外要獨立？生活中有什麼例子？）：", key=f"chat_input_{current_unit['id']}")
        if st.button("❓ 請 AI 老師解答", key=f"btn_ask_{current_unit['id']}", type="primary"):
            if q_user.strip():
                with st.spinner("AI 助教正在組織淺顯易懂的回答..."):
                    ans = unit_manager.ask_ai_tutor(q_user.strip(), current_unit['title'], current_unit.get('raw_content',''))
                    st.session_state.chat_history.append((q_user.strip(), ans))
                    logger_utils.log_ai_chat(student_info, current_unit['title'], q_user.strip(), ans)
            else:
                st.warning("請先輸入你的問題喔！")

        if st.session_state.chat_history:
            st.markdown("---")
            st.markdown("##### 📜 問答交流紀錄")
            for q_text, a_text in reversed(st.session_state.chat_history):
                with st.chat_message("user"):
                    st.write(q_text)
                with st.chat_message("assistant", avatar="🏛️"):
                    st.markdown(a_text)

    # ──────────────────────────────────────────────
    # 4. 🌱 我的足跡 (Footprint)
    # ──────────────────────────────────────────────
    with tab_footprint:
        st.markdown("### 🌱 我的自主學習足跡")
        st.caption("記錄你在每個學習單元的成長歷程。按照自己的節奏學習，每一步都是進步！")

        footprints = logger_utils.get_student_footprint(student_info)
        
        if not footprints:
            st.info("🌱 你尚未在任何單元進行「小試身手」。快挑選一個單元開始學習吧！")
        else:
            total_count = len(footprints)
            mastered_count = sum(1 for f in footprints if "🌳" in f.get("status", ""))
            accuracy_rate = round((mastered_count / total_count * 100) if total_count > 0 else 0)

            st.markdown(f"""
            <div class="observatory-strip">
                <div>
                    <strong>{total_count}</strong>
                    <span>🔭 巡航探索單元</span>
                </div>
                <div>
                    <strong>{mastered_count}</strong>
                    <span>✨ 已點亮星宿（已掌握）</span>
                </div>
                <div>
                    <strong>{accuracy_rate}%</strong>
                    <span>🎯 觀念掌握度</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            for fp in footprints:
                status_str = fp.get("status", "")
                if "🌳" in status_str:
                    badge_class = "badge-status-mastered"
                elif "🌿" in status_str:
                    badge_class = "badge-status-practice"
                else:
                    badge_class = "badge-status-look"

                weaks = fp.get("weak_tags", [])
                weak_text = f"<span style='color: #fb923c;'>需加強：{'、'.join(weaks)}</span>" if weaks else "<span style='color: #4ade80;'>全部掌握</span>"

                st.markdown(f"""
                <div class="feature-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                        <h4 style="margin: 0; color: #95c6f4; font-family: var(--font-serif); font-size: 1.15rem;">📖 {fp.get('unit_title','')}</h4>
                        <span class="{badge_class}">{status_str}</span>
                    </div>
                    <p style="margin: 0.3rem 0; color: #cbd5e1;"><b>🔄 探索次數：</b>{fp.get('practice_count',1)} 次 ｜ <b>重點概念：</b>{weak_text}</p>
                    <p style="margin: 0.3rem 0; font-size: var(--fluid-sub); color: #8ba5be;">最後巡航時間：{fp.get('last_updated','')}</p>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 👨‍🏫 教師端 (Teacher Portal)
# ══════════════════════════════════════════════
elif is_teacher_ready:
    st.markdown("""
    <div class="galaxy-header">
        <p class="eyebrow">TEACHER OBSERVATORY & CURRICULUM MANAGEMENT</p>
        <div style="display: flex; align-items: center; gap: 0.9rem;">
            <span class="brand-mark">師</span>
            <div>
                <h1 style="margin: 0; font-size: var(--fluid-h1); font-weight: 700;">教師星系觀測中心</h1>
                <p style="margin: 0.2rem 0 0 0; font-size: var(--fluid-sub); color: #8ba5be; letter-spacing: 0.05em;">教材單元智能萃取 · 全班學習航跡總覽 · AI 適性化支援</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    t_tab1, t_tab2 = st.tabs([
        "📚 我的教材",
        "📊 學習狀況"
    ])

    # ──────────────────────────────────────────────
    # 教師端 1. 📚 我的教材 (My Materials)
    # ──────────────────────────────────────────────
    with t_tab1:
        st.markdown("### 📚 教材單元管理")
        st.caption("教師可直接上傳教材檔案（.docx、.pdf、.txt、.md）或貼上課本內容，系統將自動萃取重點、整理白話內容、建立 4 則生活案例、隨機題庫與補救說明。")

        # ➕ 新增教材區
        with st.expander("➕ 新增學習單元 (支援直接上傳檔案或文字輸入)", expanded=False):
            st.markdown("#### 📁 方式一：直接上傳教材檔案（推薦）")
            uploaded_file = st.file_uploader(
                "選擇或拖曳教材檔案（支援 .docx, .pdf, .txt, .md）",
                type=["docx", "pdf", "txt", "md"],
                key="new_unit_file_uploader",
                help="系統會自動讀取檔案文字，並自動填入下方單元名稱與內容！"
            )

            # 若有上傳檔案，自動萃取並快取到 session_state
            if uploaded_file is not None:
                file_sig = f"{uploaded_file.name}_{uploaded_file.size}"
                if st.session_state.get("last_uploaded_file_sig") != file_sig:
                    s_title, s_text = safe_extract_text_from_file_upload(uploaded_file)
                    st.session_state["last_uploaded_file_sig"] = file_sig
                    st.session_state["cached_upload_title"] = s_title
                    st.session_state["cached_upload_text"] = s_text
                    st.success(f"✅ 已成功從檔案【{uploaded_file.name}】讀取 {len(s_text)} 字！已自動帶入下方表單，您可以直接建立或微調內容。")

            st.markdown("#### ✍️ 方式二：檢閱內容或手動貼上教材文字")
            with st.form("new_unit_form"):
                default_title = st.session_state.get("cached_upload_title", "")
                default_content = st.session_state.get("cached_upload_text", "")

                new_title = st.text_input("單元名稱", value=default_title, placeholder="例如：第3課：政府的組織與職權")
                new_content = st.text_area("課本教材內容", value=default_content, placeholder="請直接貼上課本段落、講義文字，或透過上方按鈕直接上傳檔案...", height=220)

                submit_create = st.form_submit_button("🚀 建立學習單元", type="primary")

                if submit_create:
                    if not new_title.strip() or not new_content.strip():
                        st.warning("請填寫單元名稱與教材內容（或透過上方上傳教材檔案）喔！")
                    else:
                        with st.spinner("🤖 AI 正在分析教材、萃取重點、建立 4 則生活案例與題庫..."):
                            created = unit_manager.create_unit(new_title.strip(), new_content.strip())
                            st.session_state.pop("cached_upload_title", None)
                            st.session_state.pop("cached_upload_text", None)
                            st.session_state.pop("last_uploaded_file_sig", None)
                            st.success(f"🎉 成功建立學習單元【{created['title']}】！已直接發布供學生使用。")
                            st.rerun()

        st.markdown("---")
        st.markdown("#### 📋 已建立的教材清單")

        current_units = unit_manager.load_all_units()
        if not current_units:
            st.info("目前尚未建立教材單元，請點擊上方「➕ 新增學習單元」建立。")
        else:
            for u in current_units:
                u_id = u.get("id")
                u_title = u.get("title")
                u_kps = u.get("key_points", [])
                u_qs = u.get("practice_questions", [])

                with st.container():
                    st.markdown(f"""
                    <div class="feature-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; color: #38bdf8;">📖 {u_title}</h4>
                            <span style="font-size: var(--fluid-sub); color: #94a3b8;">更新時間：{u.get('updated_at', u.get('created_at',''))}</span>
                        </div>
                        <p style="margin-top: 0.5rem; color: #cbd5e1;">
                            <b>📌 萃取重點：</b>{len(u_kps)} 條 ｜ <b>✏️ 小試身手題庫：</b>{len(u_qs)} 題 ｜ <b>🏫 生活案例：</b>{len(u.get('life_cases',[]))} 個
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    c_view, c_edit, c_del = st.columns([1, 1, 1])
                    with c_view:
                        if st.button("👁️ 查看教材內容", key=f"view_btn_{u_id}", use_container_width=True):
                            st.session_state[f"show_detail_{u_id}"] = not st.session_state.get(f"show_detail_{u_id}", False)
                    with c_edit:
                        if st.button("✏️ 修改教材", key=f"edit_btn_{u_id}", use_container_width=True):
                            st.session_state[f"show_edit_{u_id}"] = not st.session_state.get(f"show_edit_{u_id}", False)
                    with c_del:
                        if st.button("🗑️ 刪除單元", key=f"del_btn_{u_id}", use_container_width=True):
                            unit_manager.delete_unit(u_id)
                            st.success(f"已刪除單元【{u_title}】")
                            st.rerun()

                    # 查看內容展開
                    if st.session_state.get(f"show_detail_{u_id}", False):
                        st.markdown(f"##### 📌 核心學習重點：")
                        for p in u_kps:
                            st.markdown(f"- {p}")
                        st.markdown(f"##### 🌟 白話整理內容：")
                        st.markdown(u.get("easy_content", ""))
                        st.markdown(f"##### 🏫 生活案例 ({len(u.get('life_cases',[]))} 則)：")
                        for lc in u.get("life_cases", []):
                            st.markdown(f"- **{lc.get('title','情境實例')}**：{lc.get('story','')}")
                        st.markdown(f"##### ✏️ 小試身手練習題庫 ({len(u_qs)} 題，學生端每次隨機精選 8 題)：")
                        for idx, q in enumerate(u_qs):
                            st.markdown(f"**第 {idx+1} 題【{q.get('concept_tag','')}】**：{q.get('question','')}")
                            st.caption(f"選項：{', '.join(q.get('options',[]))}｜正確答案：選項 {q.get('correct_index',0)+1}")
                        st.markdown("---")

                    # 修改教材展開
                    if st.session_state.get(f"show_edit_{u_id}", False):
                        st.markdown("##### 📂 上傳新檔案替換教材內容（選填）：")
                        edit_file = st.file_uploader(
                            "選擇新檔案替換內容 (.docx, .pdf, .txt, .md)",
                            type=["docx", "pdf", "txt", "md"],
                            key=f"edit_file_upload_{u_id}"
                        )
                        if edit_file is not None:
                            e_sig = f"{edit_file.name}_{edit_file.size}"
                            if st.session_state.get(f"edit_sig_{u_id}") != e_sig:
                                e_title, e_text = safe_extract_text_from_file_upload(edit_file)
                                st.session_state[f"edit_sig_{u_id}"] = e_sig
                                st.session_state[f"edit_title_{u_id}"] = e_title
                                st.session_state[f"edit_text_{u_id}"] = e_text
                                st.info(f"✅ 已成功從檔案【{edit_file.name}】讀取 {len(e_text)} 字，已自動更新下方欄位！")

                        curr_t = st.session_state.get(f"edit_title_{u_id}", u_title)
                        curr_c = st.session_state.get(f"edit_text_{u_id}", u.get("raw_content", ""))

                        with st.form(f"edit_form_{u_id}"):
                            edit_t = st.text_input("修改單元名稱", value=curr_t)
                            edit_c = st.text_area("修改教材內容", value=curr_c, height=180)
                            regen = st.checkbox("🔄 是否由 AI 重新自動生成重點、4 則生活案例與隨機題庫？", value=False)
                            save_edit = st.form_submit_button("💾 儲存修改", type="primary")
                            if save_edit:
                                unit_manager.update_unit(u_id, edit_t, edit_c, regenerate=regen)
                                st.session_state[f"show_edit_{u_id}"] = False
                                st.session_state.pop(f"edit_sig_{u_id}", None)
                                st.session_state.pop(f"edit_title_{u_id}", None)
                                st.session_state.pop(f"edit_text_{u_id}", None)
                                st.success("已更新單元內容！")
                                st.rerun()

                    st.markdown("<br>", unsafe_allow_html=True)

    # ──────────────────────────────────────────────
    # 教師端 2. 📊 學習狀況 (Learning Status)
    # ──────────────────────────────────────────────
    with t_tab2:
        st.markdown("### 📊 學生學習狀況摘要")
        st.caption("簡單清楚掌握學生的學習進度與重點理解情況。")

        summary = logger_utils.get_teacher_learning_summary()

        # 頂部簡單卡片摘要
        c_sum1, c_sum2 = st.columns(2)
        with c_sum1:
            st.markdown(f"""
            <div class="summary-metric-card" style="border-left: 5px solid #22c55e;">
                <div style="font-size: var(--fluid-sub); color: #cbd5e1; margin-bottom: 0.3rem;">📅 今日學習進度</div>
                <div style="font-size: clamp(1.4rem, 1.2vw + 1rem, 1.85rem); font-weight: 800; color: #4ade80;">
                    今天有 {summary['completed_today_count']} 位學生完成學習
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c_sum2:
            attention_color = "#f87171" if summary['need_attention_count'] > 0 else "#94a3b8"
            st.markdown(f"""
            <div class="summary-metric-card" style="border-left: 5px solid {attention_color};">
                <div style="font-size: var(--fluid-sub); color: #cbd5e1; margin-bottom: 0.3rem;">💡 教學關懷提醒</div>
                <div style="font-size: clamp(1.4rem, 1.2vw + 1rem, 1.85rem); font-weight: 800; color: {attention_color};">
                    其中 {summary['need_attention_count']} 位學生可能需要老師關心
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 觀念掌握摘要
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### 🟢 學生們學習順利的重要觀念")
            if summary["smooth_concepts"]:
                for sc in summary["smooth_concepts"]:
                    st.markdown(f'<div class="key-point-card" style="border-left-color: #22c55e;">✅ <b>{sc}</b>（多數學生掌握良好）</div>', unsafe_allow_html=True)
            else:
                st.info("尚無足夠數據，待學生完成練習後自動統計。")

        with col_c2:
            st.markdown("#### 🟡 學生們需要加強學習的重要觀念")
            if summary["weak_concepts"]:
                for wc in summary["weak_concepts"]:
                    st.markdown(f'<div class="key-point-card" style="border-left-color: #f59e0b;">⚠️ <b>{wc}</b>（學生較常出現疑點，可於課堂加強提示）</div>', unsafe_allow_html=True)
            else:
                st.info("目前全體學生觀念掌握良好，無明顯常錯觀念。")

        st.markdown("---")

        # 詳細資料清單 (可點選查看)
        st.markdown("#### 👤 學生個別學習詳細資料")
        
        details = summary["student_details"]
        if not details:
            st.info("目前尚無學生紀錄。")
        else:
            for s in details:
                s_name = s.get("name", "")
                s_class = s.get("class_name", "")
                s_seat = s.get("seat_num", "")
                s_weaks = s.get("weak_concepts", [])
                s_prog = s.get("unit_progress", {})
                s_practices = s.get("total_practices", 0)

                weaks_display = f"<span style='color: #f87171;'>{', '.join(s_weaks)}</span>" if s_weaks else "<span style='color: #4ade80;'>無（掌握良好）</span>"

                with st.expander(f"👤 {s_class} 班 {s_seat} 號 — {s_name}（已練習 {len(s_prog)} 個單元，共 {s_practices} 次）"):
                    st.markdown(f"**尚未完全理解的學習重點**：{weaks_display}", unsafe_allow_html=True)
                    st.markdown(f"**最後學習時間**：`{s.get('last_active','')}`")
                    
                    st.markdown("##### 📖 各單元學習狀態：")
                    if not s_prog:
                        st.caption("尚未進行單元小試身手。")
                    else:
                        for uid, prog in s_prog.items():
                            st.write(f"- **{prog.get('unit_title','')}**：`{prog.get('status','')}` (練習 {prog.get('practice_count',1)} 次 ｜ 最近得分：{prog.get('score',0)}/{prog.get('total',0)})")

        st.markdown("---")
        # 匯出 CSV 報表
        df_csv = logger_utils.generate_csv_report()
        if not df_csv.empty:
            csv_data = df_csv.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="📥 匯出全班學習狀況 CSV 報表 (Excel 格式)",
                data=csv_data,
                file_name="全班公民學習狀況與進度摘要報表.csv",
                mime="text/csv",
                type="primary"
            )

else:
    # ══════════════════════════════════════════════
    # 🌌 歡迎啟航與引導頁面 (Welcome & Setup Guide)
    # ══════════════════════════════════════════════
    st.markdown("""
    <div class="galaxy-header">
        <p class="eyebrow">NATIONAL JUNIOR HIGH CIVICS AI LEARNING GALAXY</p>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span class="brand-mark">民</span>
                <div>
                    <h1 style="margin: 0; font-size: var(--fluid-h1); font-weight: 700; line-height: 1.2;">國中公民思辨星系 ｜ AI 智慧自主學習館</h1>
                    <p style="margin: 0.2rem 0 0 0; font-size: var(--fluid-sub); color: #8ba5be; letter-spacing: 0.05em;">歷屆觀念導引・法政思辨啟蒙・AI 助教陪伴自主成長</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 🚀 加大強調「航行準備中 ｜ 請先完成左欄資料登記」
    st.markdown("""
    <div style="background: rgba(22, 46, 82, 0.85); border: 2.5px solid #f4d38b; border-radius: 18px; padding: 2.2rem 2.5rem; margin: 1.5rem 0 2rem 0; text-align: center; box-shadow: 0 12px 35px rgba(0, 0, 0, 0.45), 0 0 20px rgba(244, 211, 139, 0.15);">
        <div style="display: inline-flex; align-items: center; justify-content: center; gap: 0.9rem; margin-bottom: 0.8rem;">
            <span class="pulse-dot" style="width: 0.85rem; height: 0.85rem; background: #f4d38b; box-shadow: 0 0 14px #f4d38b;"></span>
            <h2 style="margin: 0; font-family: var(--font-serif); font-size: var(--fluid-h2); font-weight: 900; color: #ffffff; letter-spacing: 0.04em;">
                航行準備中 ｜ 請先完成左欄資料登記
            </h2>
        </div>
        <p style="margin: 0.4rem 0 0 0; font-size: clamp(1.08rem, 0.4vw + 1rem, 1.25rem); color: #f4d38b; font-weight: 700; letter-spacing: 0.04em;">
            👈 請由左側邊欄選定操作身分、填寫班級座號姓名並挑選學習單元，即可立即啟航開展學習！
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.user_role == "teacher" and not st.session_state.is_teacher_authenticated:
        st.warning("🔒 **教師身分確認**：進入教師管理端需要驗證教師專屬密碼。")
        if st.button("🔑 開啟教師密碼驗證視窗", type="primary"):
            teacher_auth_dialog()

    # 🌟 星系特色功能導覽（精簡版）
    st.markdown("""
    <div style="margin-top: 1.5rem;">
        <h3 style="color: #95c6f4; font-family: var(--font-serif); font-size: var(--fluid-h3); margin-bottom: 0.9rem;">
            🌟 星系特色功能導覽
        </h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
            <div class="feature-card" style="margin-bottom: 0; padding: 1.1rem 1.3rem;">
                <h4 style="color: #95c6f4; margin: 0 0 0.35rem 0; font-size: 1.18rem; font-weight: 700;">📖 白話重點 ＆ 直式心智圖</h4>
                <p style="color: #cbd5e1; font-size: var(--fluid-body); margin: 0; line-height: 1.6;">輕鬆看懂核心重點，直式心智圖清晰免橫滑。</p>
            </div>
            <div class="feature-card" style="margin-bottom: 0; padding: 1.1rem 1.3rem;">
                <h4 style="color: #95c6f4; margin: 0 0 0.35rem 0; font-size: 1.18rem; font-weight: 700;">✏️ 素養情境隨機小試身手</h4>
                <p style="color: #cbd5e1; font-size: var(--fluid-body); margin: 0; line-height: 1.6;">生活情境無壓力練習，每次隨機抽題與洗牌選項，錯題即享白話充電與避坑口訣。</p>
            </div>
            <div class="feature-card" style="margin-bottom: 0; padding: 1.1rem 1.3rem;">
                <h4 style="color: #95c6f4; margin: 0 0 0.35rem 0; font-size: 1.18rem; font-weight: 700;">💬 公民 AI 助教隨身問</h4>
                <p style="color: #cbd5e1; font-size: var(--fluid-body); margin: 0; line-height: 1.6;">隨選即問，AI 老師以校園日常案例親切解惑。</p>
            </div>
            <div class="feature-card" style="margin-bottom: 0; padding: 1.1rem 1.3rem;">
                <h4 style="color: #95c6f4; margin: 0 0 0.35rem 0; font-size: 1.18rem; font-weight: 700;">🌱 自主成長學習足跡</h4>
                <p style="color: #cbd5e1; font-size: var(--fluid-body); margin: 0; line-height: 1.6;">點亮個人探索星宿，無排名壓力、自主步調進步。</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

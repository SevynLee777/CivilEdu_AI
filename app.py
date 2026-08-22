import streamlit as st
import data_loader
import logger_utils
import google.generativeai as genai
import os
import json
import random
import html
from dotenv import load_dotenv

# --- Load Config ---
config = data_loader.load_config()
subject_name = config.get("subject_name", "國中八年級公民")
assistant_role = config.get("assistant_role", "國中八年級公民科 AI 助教")

# --- Page Config ---
st.set_page_config(
    page_title=f"{subject_name} 適性診斷與補強學習平台",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_dotenv()

# --- Custom Styling & High-Contrast Design System ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Noto Sans TC', -apple-system, sans-serif;
    }
    
    /* Main Background & Cards */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc !important;
    }
    
    /* Standard Text Element Override */
    .stMarkdown p, .stMarkdown span, .stMarkdown strong, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #f8fafc !important;
    }
    
    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.35) 0%, rgba(168, 85, 247, 0.35) 50%, rgba(236, 72, 153, 0.3) 100%);
        backdrop-filter: blur(16px);
        border: 1.5px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    }
    
    .hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        font-size: 1.1rem;
        color: #f1f5f9 !important;
        font-weight: 500;
        margin-bottom: 1.2rem;
    }

    .badge-pill {
        display: inline-block;
        background: rgba(99, 102, 241, 0.45);
        border: 1.5px solid #818cf8;
        color: #ffffff !important;
        font-size: 0.9rem;
        font-weight: 700;
        padding: 5px 14px;
        border-radius: 20px;
        margin-right: 8px;
        margin-bottom: 6px;
    }

    /* Onboarding Card */
    .onboarding-card {
        background: rgba(30, 41, 59, 0.95);
        border: 2px solid #6366f1;
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
        max-width: 800px;
        margin: 2rem auto;
    }

    /* Tabs Header Bar (主頁籤按鈕與選單高對比) */
    div[data-testid="stTabs"] {
        background-color: transparent !important;
        border-bottom: 2px solid #6366f1 !important;
        margin-bottom: 1.5rem !important;
    }

    div[data-testid="stTabs"] button,
    button[data-baseweb="tab"] {
        background-color: #1e293b !important;
        border: 2px solid #475569 !important;
        border-bottom: none !important;
        border-radius: 12px 12px 0px 0px !important;
        margin-right: 8px !important;
        padding: 0.8rem 1.6rem !important;
        transition: all 0.2s ease !important;
    }

    div[data-testid="stTabs"] button p,
    div[data-testid="stTabs"] button span,
    div[data-testid="stTabs"] button div,
    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] span,
    button[data-baseweb="tab"] div {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        opacity: 1 !important;
    }

    /* Selected Tab (目前點選的主頁籤：鮮亮金黃文字與強大靛紫背景) */
    div[data-testid="stTabs"] button[aria-selected="true"],
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%) !important;
        border: 2px solid #818cf8 !important;
        border-bottom: 4px solid #fef08a !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.5) !important;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] p,
    div[data-testid="stTabs"] button[aria-selected="true"] span,
    div[data-testid="stTabs"] button[aria-selected="true"] div,
    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span,
    button[data-baseweb="tab"][aria-selected="true"] div {
        color: #fef08a !important;
        -webkit-text-fill-color: #fef08a !important;
        font-size: 1.18rem !important;
        font-weight: 900 !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6) !important;
    }

    /* Sidebar High Contrast (側邊欄文字與按鈕高對比) */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] strong {
        color: #ffffff !important;
        font-weight: 600;
    }

    /* Sidebar Buttons (左側欄「重測起點程度 / 修改資料」按鈕高對比) */
    section[data-testid="stSidebar"] div.stButton > button,
    section[data-testid="stSidebar"] button {
        background: linear-gradient(135deg, #312e81 0%, #4338ca 100%) !important;
        border: 2px solid #818cf8 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
        padding: 0.75rem 1rem !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] div.stButton > button p,
    section[data-testid="stSidebar"] div.stButton > button span,
    section[data-testid="stSidebar"] div.stButton > button div,
    section[data-testid="stSidebar"] button p,
    section[data-testid="stSidebar"] button span,
    section[data-testid="stSidebar"] button div {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 1.08rem !important;
        font-weight: 800 !important;
        opacity: 1 !important;
    }

    section[data-testid="stSidebar"] div.stButton > button:hover,
    section[data-testid="stSidebar"] button:hover {
        background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%) !important;
        border-color: #fef08a !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(99, 102, 241, 0.6) !important;
    }

    /* High-Contrast Inputs & Text Areas (輸入框與標題文字) */
    label[data-testid="stWidgetLabel"], 
    div[data-testid="stWidgetLabel"] p, 
    label p,
    .stSelectbox label, 
    .stTextInput label {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.4rem !important;
    }

    /* Selectbox Control Container (下拉選單框體) */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        border: 1.8px solid #6366f1 !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }

    div[data-baseweb="select"] span, 
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] input {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 1.08rem !important;
        font-weight: 600 !important;
    }

    /* Selectbox Dropdown Menu Options (下拉選單選項文字) */
    div[data-baseweb="popover"] ul,
    div[data-baseweb="menu"] {
        background-color: #1e293b !important;
        border: 1.5px solid #6366f1 !important;
    }

    div[data-baseweb="popover"] li,
    div[data-baseweb="menu"] [role="option"] {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background-color: #1e293b !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="menu"] [role="option"]:hover {
        background-color: #312e81 !important;
        color: #818cf8 !important;
    }

    /* Text Inputs (文字輸入框高對比) */
    .stTextInput input, div[data-baseweb="input"] input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: 1.8px solid #6366f1 !important;
        border-radius: 10px !important;
        font-size: 1.08rem !important;
        font-weight: 600 !important;
    }

    .stTextInput input::placeholder {
        color: #94a3b8 !important;
        -webkit-text-fill-color: #94a3b8 !important;
    }

    .stTextArea textarea, div[data-baseweb="textarea"] textarea {
        background-color: #1e293b !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 1.08rem !important;
        line-height: 1.7 !important;
        border: 1.5px solid #64748b !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
    }
    
    .stTextArea textarea:disabled, div[data-baseweb="textarea"] textarea:disabled {
        background-color: #0f172a !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        opacity: 1 !important;
    }

    /* Alerts High Contrast (Info, Warning, Success, Error 訊息框高對比) */
    div[data-testid="stAlert"] {
        background-color: #1e293b !important;
        border-radius: 12px !important;
        border: 1.5px solid #6366f1 !important;
        color: #ffffff !important;
    }

    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] div,
    div[data-testid="stAlert"] span {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }

    /* Expander High Contrast (折疊面板標題與內容高對比) */
    div[data-testid="stExpander"] details {
        background-color: #1e293b !important;
        border: 1.5px solid #64748b !important;
        border-radius: 12px !important;
    }

    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span {
        color: #ffffff !important;
        font-size: 1.08rem !important;
        font-weight: 700 !important;
    }

    /* Metric High Contrast (指標數據高對比) */
    div[data-testid="stMetricLabel"] p {
        color: #e2e8f0 !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetricValue"] div {
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }

    /* Chat Messages (AI 對話視窗高對比) */
    div[data-testid="stChatMessage"] {
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }

    div[data-testid="stChatMessage"] p {
        color: #ffffff !important;
        font-size: 1.05rem !important;
        line-height: 1.75 !important;
    }

    /* High-Contrast Material Reader Container */
    .reader-container {
        background: #0f172a;
        color: #ffffff !important;
        border: 2px solid #6366f1;
        border-radius: 16px;
        padding: 2rem;
        font-size: 1.12rem;
        line-height: 1.85;
        max-height: 580px;
        overflow-y: auto;
        box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.6), 0 10px 30px rgba(0, 0, 0, 0.4);
        white-space: pre-wrap;
        word-wrap: break-word;
        letter-spacing: 0.3px;
    }
    
    .reader-container::-webkit-scrollbar {
        width: 10px;
    }
    .reader-container::-webkit-scrollbar-track {
        background: #1e293b;
        border-radius: 8px;
    }
    .reader-container::-webkit-scrollbar-thumb {
        background: #818cf8;
        border-radius: 8px;
    }
    
    /* High-Contrast Radio Option Labels (選擇題與診斷題選項高對比) */
    div[data-testid="stRadio"] div[role="radiogroup"] label {
        background: #1e293b !important;
        border: 1.5px solid #64748b !important;
        border-radius: 10px !important;
        padding: 0.6rem 1rem !important;
        margin-bottom: 0.5rem !important;
        cursor: pointer !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
        border-color: #818cf8 !important;
        background: #312e81 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label p,
    div[data-testid="stRadio"] div[role="radiogroup"] label span,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 1.08rem !important;
        font-weight: 600 !important;
    }

    /* Question Text Box High Contrast */
    .q-box {
        background: rgba(30, 41, 59, 0.95);
        border-left: 5px solid #818cf8;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        font-size: 1.12rem;
        font-weight: 700;
        color: #ffffff !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 12px;
        font-weight: 700;
        font-size: 1rem;
        padding: 0.6rem 1.5rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        color: white !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }
    
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# --- API Setup ---
try:
    api_key = st.secrets.get("GEMINI_API_KEY", None)
except Exception:
    api_key = None

if not api_key:
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    with st.sidebar:
        st.markdown("### ⚙️ API 金鑰設定")
        api_key = st.text_input("Gemini API Key", type="password", help="請輸入您的 Google Gemini API Key")
        if not api_key:
            st.warning("請輸入 Gemini API Key 以啟動 AI 學習功能")
            st.stop()

genai.configure(api_key=api_key)

# --- Robust Model Caller with Fallback ---
def call_gemini_api(prompt, generation_config=None):
    candidate_models = [
        'gemini-3.5-flash',
        'gemini-flash-latest',
        'gemini-2.0-flash',
        'gemini-2.5-flash-lite',
        'gemini-pro-latest'
    ]
    
    last_exception = None
    for m_name in candidate_models:
        try:
            m = genai.GenerativeModel(m_name)
            if generation_config:
                res = m.generate_content(prompt, generation_config=generation_config)
            else:
                res = m.generate_content(prompt)
            return res
        except Exception as e:
            last_exception = e
            continue
            
    raise last_exception

# --- Session State Management ---
if "student_profile" not in st.session_state:
    st.session_state.student_profile = None
if "diagnostic_completed" not in st.session_state:
    st.session_state.diagnostic_completed = False
if "diagnostic_result" not in st.session_state:
    st.session_state.diagnostic_result = None
if "diagnostic_step" not in st.session_state:
    st.session_state.diagnostic_step = "profile"
if "current_diagnostic_qs" not in st.session_state:
    st.session_state.current_diagnostic_qs = None
if "current_topic" not in st.session_state:
    st.session_state.current_topic = None
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "graded" not in st.session_state:
    st.session_state.graded = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Diagnostic Baseline Questions (起點能力診斷測驗 5 題) ---
DIAGNOSTIC_QUESTION_POOLS = [
    [
        {
            "id": "diag_1_1",
            "q": "1. 關於「國家組成四大要素」，下列何者非國家行使主權所必須的傳統四要素之一？",
            "options": ["A) 人民", "B) 領土", "C) 政府", "D) 邦交國"],
            "correct_index": 3,
            "explanation": "國家的四要素為人民、領土、政府、主權。邦交國屬於外交互動，非組成國家的內部必要要素。"
        },
        {
            "id": "diag_1_2",
            "q": "1. 關於國家的「主權」概念，下列敘述何者正確？",
            "options": ["A) 主權對內具有最高性，對外具有獨立性", "B) 主權可由鄰國或國際組織代為行使", "C) 無設戶籍的外籍人士亦享有國家主權", "D) 領土範圍不屬於國家主權行使的範疇"],
            "correct_index": 0,
            "explanation": "主權是指國家對內擁有最高權力，對外不受他國干涉與控制。"
        }
    ],
    [
        {
            "id": "diag_2_1",
            "q": "2. 在民主政治中，「政府施政失敗時，政務官員須下臺負責」這屬於哪一項民主政治原則？",
            "options": ["A) 責任政治", "B) 民意政治", "C) 法治政治", "D) 政黨政治"],
            "correct_index": 0,
            "explanation": "政務官員對政策與施政後果負責並向國人請辭，屬於「責任政治」的體現。"
        },
        {
            "id": "diag_2_2",
            "q": "2. 全民透過投票選出縣市長與民意代表，這最能體現下列哪一項民主政治原則？",
            "options": ["A) 責任政治", "B) 民意政治", "C) 法治政治", "D) 政黨政治"],
            "correct_index": 1,
            "explanation": "政府權力來自人民授權，施政須符合多數民意，稱為「民意政治」。"
        }
    ],
    [
        {
            "id": "diag_3_1",
            "q": "3. 我國廣義的法律三位階（憲法、法律、命令）中，何者效力最高，且修改程序最嚴格？",
            "options": ["A) 命令", "B) 法律", "C) 憲法", "D) 自治條例"],
            "correct_index": 2,
            "explanation": "憲法是國家的根本大法，具有最高位階與最高效力，修改程序亦最嚴格。"
        },
        {
            "id": "diag_3_2",
            "q": "3. 當行政機關發布的「命令」與立法院通過的「法律」內容相互抵觸時，其效力為何？",
            "options": ["A) 命令優先有效", "B) 該命令無效", "C) 兩者皆有效", "D) 由法院隨機指定"],
            "correct_index": 1,
            "explanation": "依據法律位階原則，下位階之命令不得牴觸上位階之法律與憲法，牴觸者無效。"
        }
    ],
    [
        {
            "id": "diag_4_1",
            "q": "4. 小明在網路上公開且理性地發表對時事的看法，這屬於憲法保障的哪一種基本權利？",
            "options": ["A) 平等權", "B) 自由權", "C) 受益權", "D) 參政權"],
            "correct_index": 1,
            "explanation": "發表言論屬於憲法第11條保障之「言論自由」，歸屬於自由權範疇。"
        },
        {
            "id": "diag_4_2",
            "q": "4. 年滿20歲的中華民國國民依法享有投票選舉公職人員的權利，這屬於何種基本權利？",
            "options": ["A) 平等權", "B) 自由權", "C) 受益權", "D) 參政權"],
            "correct_index": 3,
            "explanation": "選舉、罷免、創制、複決等參與政治運作之權利，屬於「參政權」。"
        }
    ],
    [
        {
            "id": "diag_5_1",
            "q": "5. 我國中央政府設有行政、立法、司法、考試、監察五院，其運作的核心精神為何？",
            "options": ["A) 集中權力於單一機關", "B) 權力分立與相互制衡", "C) 增加政府官員人數", "D) 簡化公務員考選手續"],
            "correct_index": 1,
            "explanation": "五院分權的核心精神為「權力分立與相互制衡」，避免單一機關權力過大侵害人民權利。"
        },
        {
            "id": "diag_5_2",
            "q": "5. 我國最高立法機關為「立法院」，下列何者屬於立法院的主要職權？",
            "options": ["A) 執行國家法律", "B) 審議法律案與中央政府總預算案", "C) 掌理公務人員懲戒", "D) 負責違憲審判"],
            "correct_index": 1,
            "explanation": "立法院為國家最高立法機關，主要職權包含制定修訂法律、審議政府總預算及監督行政院。"
        }
    ]
]

def get_random_diagnostic_questions():
    selected_qs = []
    for domain in DIAGNOSTIC_QUESTION_POOLS:
        selected_qs.append(random.choice(domain))
    return selected_qs

# --- AI Helper Functions ---
def generate_mastery_quiz(topic_name, topic_text):
    """Generates a key-concept mastery quiz based on the entered textbook material."""
    prompt = f"""
    你是【{assistant_role}】。請依據老師在後台輸入的課本講義教材（單元：{topic_name}），設計一份「重點精熟自主檢測題」。
    全體內容必須使用 **繁體中文**。

    教材內容：
    {topic_text[:15000]}

    要求規範：
    1. 生成 3 題選擇題 (MCQ)，用於精準檢測學生對課本核心重點的理解情況。
    2. 生成 1 題素養簡答題 (Short Answer)，測試學生對該單元核心觀念的表達與應用。
    3. 每題須明確指定考點標籤（如：國家要素、憲法位階、自由權限制等）。

    請嚴格輸出 JSON 格式如下：
    {{
        "mcq": [
            {{
                "q": "題目內容...",
                "options": ["A) 選項 1", "B) 選項 2", "C) 選項 3", "D) 選項 4"],
                "correct_index": 0,
                "concept_tag": "考點標籤",
                "explanation": "答題解析說明..."
            }}
        ],
        "sa": [
            {{
                "q": "簡答題目...",
                "concept_tag": "考點標籤",
                "reference_answer": "參考解答重點與核心概念..."
            }}
        ]
    }}
    """
    try:
        response = call_gemini_api(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        st.error(f"生成精熟檢測題時發生錯誤: {e}")
        return None

def generate_remedial_material(topic_name, topic_text, mastery_level, weak_tags):
    """Generates tailored remedial study material including summary, mind map, and detailed notes based on student's mastery level and weakness tags."""
    weak_str = ", ".join(weak_tags) if weak_tags else "基礎觀念鞏固"
    prompt = f"""
    你是【{assistant_role}】。
    學生在單元【{topic_name}】的自主檢測中，評定等級為：【{mastery_level}】。
    需要重點補強的弱點標籤為：【{weak_str}】。

    請依據課本講義內容：
    {topic_text[:10000]}

    請為該學生生成一份結構清晰、圖文並茂的【適性補強學習講義與心智圖】：

    請嚴格依照以下三大結構輸出 Markdown 內容：

    ### 📌 1. 核心觀念濃縮摘要 (1分鐘快讀速覽)
    - **【重點精華速記】**：用 3-4 個條點，精簡歸納本單元最重要的核心考點，特別針對弱點標籤【{weak_str}】進行特別醒目標示與說明。
    - **【觀念避坑卡片】**：列出 2 個學生最容易混淆、考錯的概念或定義，並給予一句話判斷口訣。

    ### 🧠 2. 核心觀念心智圖 (Concept Mind Map)
    請使用 Mermaid 語法繪製一幅心智圖/架構圖，必須包裹在標準的 ```mermaid 與 ``` 程式碼區塊中。
    語法要求：
    - 開頭使用 `graph TD`。
    - 主節點為「{topic_name}」。
    - 分支必須包含：核心概念、重點弱點標籤【{weak_str}】、常考考點與生活實例。
    - 節點內文字若有括號或特殊符號，請務必用雙引號包裹（例如：A["主題(定義)"] --> B["重點概念"]）。

    ### 📖 3. 專屬適性補強講義 (重點觀念剖析)
    根據學生的精熟等級【{mastery_level}】進行深度引導：
    1. 若為 🔴 待加強：提供「白話重點懶人包 + 生活實例對照 + 觀念深度澄清」。
    2. 若為 🟡 基礎級：提供「核心觀念圖解指引 + 易混淆考點對比 + 會考叮嚀」。
    3. 若為 🟢 精熟級：提供「高階觀念延伸思考 + 深度會考題型拆解與變型解析」。

    請保持親切、鼓勵且專業的國中教師口吻。
    """
    try:
        response = call_gemini_api(prompt)
        return response.text
    except Exception as e:
        return f"適性補強講義生成失敗: {e}"

def grade_sa(question, student_answer, reference, student_level="Level B"):
    prompt = f"""
    你是【{assistant_role}】，請針對八年級學生（程度：{student_level}）的回答給予鼓勵性的批改與引導。

    題目：{question}
    參考重點：{reference}
    學生回答：{student_answer}

    批改要求：
    1. 給予【評分與等級】（如：🌟 太棒了！完美掌握觀念 / 👍 表現不錯 / 💡 觀念稍有混淆）。
    2. 給予【優點鼓勵】與【建議補強】，語氣溫和親切。
    3. 用白話文補充正確觀念。
    """
    try:
        response = call_gemini_api(prompt)
        return response.text
    except Exception as e:
        return f"AI 批改暫時無法完成: {e}"

def ask_civics_ai(question, topic_name, topic_context, student_level="Level B"):
    prompt = f"""
    你是【{assistant_role}】，正在為八年級國中生解答公民科問題。
    當前單元：{topic_name}
    講義資料：{topic_context[:8000]}
    學生提問：{question}

    回答原則：
    1. 親切活潑，善用日常生活實例與校園比喻。
    2. 條列重點，用白話文補充說明。
    """
    try:
        response = call_gemini_api(prompt)
        return response.text
    except Exception as e:
        return f"解答回答失敗: {e}"


# ══════════════════════════════════════════════
# 學生登錄與起點程度前測流程 (Onboarding Portal)
# ══════════════════════════════════════════════
if not st.session_state.diagnostic_completed:
    st.markdown("""
    <div style="text-align: center; margin-top: 1rem; margin-bottom: 2rem;">
        <h1 style="font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #a5b4fc, #f472b6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🎓 國中八年級公民 — 學生學習檢測與適性補強平台
        </h1>
        <p style="color: #cbd5e1; font-size: 1.1rem;">
            請填寫班級座號並完成 5 題公民起點診斷，平台將為您調配最佳檢測與補強教材！
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.diagnostic_step == "profile":
        with st.form("profile_form"):
            st.markdown("### 📝 第一步：登記學生基本資料")
            class_options = [str(i) for i in range(801, 822)]
            seat_options = [f"{i:02d}" for i in range(1, 31)]

            c1, c2, c3 = st.columns(3)
            with c1:
                class_name = st.selectbox("🏫 班級 (選擇 801 ~ 821)", class_options)
            with c2:
                seat_num = st.selectbox("🔢 座號 (選擇 01 ~ 30)", seat_options)
            with c3:
                student_name = st.text_input("👤 學生姓名", value="", placeholder="請輸入姓名 (例如: 王大明)")
            
            submit_profile = st.form_submit_button("🚀 下一步：進入公民起點能力診斷測驗", type="primary")
            if submit_profile:
                if not student_name.strip():
                    st.warning("請填寫學生姓名喔！")
                else:
                    st.session_state.student_profile = {
                        "name": student_name.strip(),
                        "class_name": class_name,
                        "seat_num": seat_num
                    }
                    st.session_state.diagnostic_step = "test"
                    st.session_state.current_diagnostic_qs = get_random_diagnostic_questions()
                    st.rerun()

    elif st.session_state.diagnostic_step == "test":
        st.markdown(f"### 🎯 第二步：起點程度診斷測驗 (共 5 題)")
        prof = st.session_state.student_profile
        st.info(f"👤 應試學生：**{prof['class_name']} 班 {prof['seat_num']} 號 — {prof['name']}**")
        
        if st.session_state.current_diagnostic_qs is None:
            st.session_state.current_diagnostic_qs = get_random_diagnostic_questions()
            
        diag_qs = st.session_state.current_diagnostic_qs
        
        with st.form("diagnostic_quiz_form"):
            diag_user_answers = {}
            for q in diag_qs:
                st.markdown(f'<div class="q-box">{q["q"]}</div>', unsafe_allow_html=True)
                diag_user_answers[q['id']] = st.radio(
                    f"選擇答案 ({q['id']})",
                    q['options'],
                    key=f"diag_{q['id']}",
                    label_visibility="collapsed"
                )
                st.markdown("---")
            
            submit_diag = st.form_submit_button("📊 送出測驗並分析我的起點程度", type="primary")
            if submit_diag:
                score = 0
                for q in diag_qs:
                    ans = diag_user_answers[q['id']]
                    if ans == q['options'][q['correct_index']]:
                        score += 1
                
                if score <= 2:
                    level = "Level A"
                    level_name = "🌱 基礎累積型"
                elif score <= 4:
                    level = "Level B"
                    level_name = "🌿 觀念進階型"
                else:
                    level = "Level C"
                    level_name = "🌳 核心素養專家型"

                diag_res = {
                    "score": score,
                    "level": level,
                    "level_name": level_name
                }
                st.session_state.diagnostic_result = diag_res
                logger_utils.save_student_profile(st.session_state.student_profile, diag_res)
                st.session_state.diagnostic_step = "done"
                st.rerun()

    elif st.session_state.diagnostic_step == "done":
        prof = st.session_state.student_profile
        res = st.session_state.diagnostic_result
        
        st.markdown(f"""
        <div class="onboarding-card">
            <h2 style="color: #a5b4fc; text-align: center; margin-bottom: 1rem;">🎉 診斷分析完成！</h2>
            <p style="font-size: 1.1rem; text-align: center;">
                <b>{prof['class_name']} 班 {prof['seat_num']} 號 {prof['name']}</b> 同學，您好！
            </p>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 1.5rem; border-radius: 12px; margin: 1.5rem 0;">
                <div style="font-size: 1.2rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.5rem;">
                    🎯 診斷得分：{res['score']} / 5 題 ({res['score']*20} 分)
                </div>
                <div style="font-size: 1.4rem; font-weight: 800; color: #f472b6; margin-bottom: 1rem;">
                    🎓 起點能力評定：{res['level_name']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("✨ 進入【公民學習精熟與適性補強平台】", type="primary", use_container_width=True):
                st.session_state.diagnostic_completed = True
                st.rerun()

    st.stop()

# ══════════════════════════════════════════════
# 主介面內容 (Main Platform Dashboard)
# ══════════════════════════════════════════════

prof = st.session_state.get("student_profile") or {"name": "學生", "class_name": "801", "seat_num": "01"}
res = st.session_state.get("diagnostic_result") or {"score": 3, "level": "Level B", "level_name": "🌿 觀念進階型"}

st.markdown(f"""
<div class="hero-banner">
    <div class="hero-title">🏛️ 國中八年級公民 — 精熟自主檢測與適性補強平台</div>
    <div class="hero-subtitle">自主自我檢測重點精熟度 · AI 自動診斷弱點觀念 · 提供適性補強教材與教師歷程追蹤</div>
    <div>
        <span class="badge-pill">👤 {prof['class_name']}班 {prof['seat_num']}號 {prof['name']}</span>
        <span class="badge-pill">🎓 起點程度：{res['level_name']}</span>
        <span class="badge-pill">✨ 適性化補強中</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
materials = data_loader.load_materials()
if not materials:
    st.error("❌ 找不到教材檔案！請老師在後台 `materials/` 資料夾中放課本 `.docx` 講義檔案。")
    st.stop()

topic_list = list(materials.keys())

with st.sidebar:
    st.markdown(f"### 👤 學生資訊")
    st.markdown(f"**姓名**：`{prof['name']}`")
    st.markdown(f"**班級**：`{prof['class_name']}`｜**座號**：`{prof['seat_num']} 號`")
    
    if st.button("🔄 重測起點程度 / 修改資料", use_container_width=True):
        st.session_state.diagnostic_completed = False
        st.session_state.diagnostic_step = "profile"
        st.session_state.current_diagnostic_qs = None
        st.rerun()

    st.markdown("---")
    st.markdown("### 📚 課本單元選擇")
    selected_topic = st.selectbox("請選擇課本學習單元", topic_list)
    
    st.markdown("---")
    st.markdown("### 🎯 學習三部曲")
    st.info("""
    - **Step 1** 進行單元精熟自主檢測
    - **Step 2** 查看精熟報告與適性補強講義
    - **Step 3** 使用 AI 隨問隨答掃除不懂的疑問
    """)

# 重置單元 state
if selected_topic != st.session_state.current_topic:
    st.session_state.current_topic = selected_topic
    st.session_state.quiz_data = None
    st.session_state.user_answers = {}
    st.session_state.graded = False

# --- Main Navigation Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 單元精熟自主檢測", 
    "📚 精熟診斷與適性補強教材", 
    "💡 公民 AI 素養問答小助手",
    "👨‍🏫 教師學習歷程後台"
])

# ══════════════════════════════════════════════
# TAB 1：單元精熟自主檢測 (Self-Test Quiz)
# ══════════════════════════════════════════════
with tab1:
    st.markdown(f"### 🎯 當前檢測單元：{selected_topic}")
    st.caption("透過 3 題核心重點選擇題與 1 題素養簡答題，自我檢測是否已精熟課本學習重點。")
    
    if st.session_state.quiz_data is None:
        st.info(f"💡 準備進行【**{selected_topic}**】的核心重點精熟自主檢測。")
        if st.button("🚀 開始自主檢測 (Start Assessment)", type="primary"):
            with st.spinner("🤖 AI 正在閱讀課本教材並分析核心重點出題..."):
                text_content = materials[selected_topic]
                quiz = generate_mastery_quiz(selected_topic, text_content)
                if quiz:
                    st.session_state.quiz_data = quiz
                    st.rerun()

    if st.session_state.quiz_data:
        quiz = st.session_state.quiz_data

        with st.form("mastery_quiz_form"):
            st.markdown("#### 🔹 第一部分：課本核心重點選擇檢測 (MCQ)")
            mcq_answers = {}
            for i, q in enumerate(quiz["mcq"]):
                st.markdown(f'<div class="q-box">第 {i+1} 題【考點：{q.get("concept_tag","核心觀念")}】：{q["q"]}</div>', unsafe_allow_html=True)
                mcq_answers[i] = st.radio(
                    f"請選擇第 {i+1} 題答案",
                    q["options"],
                    key=f"mcq_{i}",
                    label_visibility="collapsed",
                )
                st.markdown("---")

            st.markdown("#### 🔹 第二部分：素養應用與核心觀念表達 (Short Answer)")
            sa_answers = {}
            for i, q in enumerate(quiz["sa"]):
                st.markdown(f"**題目【考點：{q.get('concept_tag','觀念表達')}】：{q['q']}**")
                sa_answers[i] = st.text_area("請寫下你的理解與想法:", key=f"sa_{i}", height=120)

            submitted = st.form_submit_button("📝 繳交檢測卷並查看精熟診斷 (Submit)")
            if submitted:
                st.session_state.graded = True
                st.session_state.user_answers = {"mcq": mcq_answers, "sa": sa_answers}
                st.rerun()

    if st.session_state.graded and st.session_state.quiz_data:
        st.divider()
        st.markdown("### 📊 自主檢測成績與精熟診斷")

        quiz = st.session_state.quiz_data
        u_ans = st.session_state.user_answers

        score = 0
        total = len(quiz["mcq"])
        weak_tags = []

        for i, q in enumerate(quiz["mcq"]):
            user_choice = u_ans["mcq"][i]
            correct_choice = q["options"][q["correct_index"]]
            if user_choice == correct_choice:
                score += 1
            else:
                weak_tags.append(q.get("concept_tag", "核心觀念"))

        pct = (score / total) * 100
        if pct >= 80:
            mastery_level = "🟢 精熟級"
            mastery_desc = "🎉 太優秀了！您已高度精熟本單元的課本核心重點！"
        elif pct >= 60:
            mastery_level = "🟡 基礎級"
            mastery_desc = "👍 表現良好！已掌握大部分重點，少數觀念需要再鞏固。"
        else:
            mastery_level = "🔴 待加強"
            mastery_desc = "📖 本單元核心重點需要加強！建議前往「適性補強教材」研讀補強。"

        c_sc, c_lv = st.columns([1, 2])
        with c_sc:
            st.metric("選擇題精熟得分", f"{score} / {total}", delta=f"{int(pct)}%")
        with c_lv:
            st.markdown(f"#### 評定精熟狀態：**{mastery_level}**")
            st.info(mastery_desc)

        if weak_tags:
            st.warning(f"⚠️ **系統偵測需補強的觀念標籤**：`{'` `'.join(weak_tags)}`")

        st.markdown("#### 🧐 題目詳解與概念對照")
        for i, q in enumerate(quiz["mcq"]):
            user_choice = u_ans["mcq"][i]
            correct_choice = q["options"][q["correct_index"]]
            
            with st.expander(f"第 {i+1} 題 【考點：{q.get('concept_tag','')}】 {'✅ 答對' if user_choice == correct_choice else '❌ 答錯'}"):
                st.markdown(f"**題目**：{q['q']}")
                st.markdown(f"**你的答案**：`{user_choice}`")
                st.markdown(f"**正確答案**：`{correct_choice}`")
                st.markdown(f"💡 **解析**：{q.get('explanation', '')}")

        st.markdown("#### 📝 簡答題 AI 老師引導評語")
        sa_logs = []
        for i, q in enumerate(quiz["sa"]):
            user_text = u_ans["sa"][i]
            if not user_text.strip():
                st.warning("（未填寫簡答題回答）")
                continue
            
            with st.spinner("AI 老師正在閱卷並準備觀念引導..."):
                feedback = grade_sa(q["q"], user_text, q["reference_answer"], student_level=res['level_name'])
                sa_logs.append({
                    "question": q["q"],
                    "answer": user_text,
                    "feedback": feedback
                })
            
            st.markdown(f"**題目**：{q['q']}")
            st.info(f"**你的回答**：\n{user_text}")
            st.success(f"**🤖 AI 評語與建議**：\n{feedback}")

        # Save test result and weak tags to student log
        if not st.session_state.get("logged_mastery_" + selected_topic):
            logger_utils.log_mastery_test(prof, selected_topic, score, total, pct, mastery_level, weak_tags, sa_logs)
            st.session_state["logged_mastery_" + selected_topic] = True

        st.success("👉 請切換至 **【📚 精熟診斷與適性補強教材】** 頁籤，讀取為您量身打造的補強講義！")

        if st.button("🔄 重新檢測本單元"):
            st.session_state.quiz_data = None
            st.session_state.graded = False
            st.session_state["logged_mastery_" + selected_topic] = False
            st.rerun()

# ══════════════════════════════════════════════
# TAB 2：精熟診斷與適性補強教材 (Tailored Remediation)
# ══════════════════════════════════════════════
with tab2:
    st.markdown(f"### 📚 專屬適性補強教材 — {selected_topic}")
    
    # Check if student completed mastery test
    if not st.session_state.graded or st.session_state.quiz_data is None:
        st.warning("💡 請先至 **【🎯 單元精熟自主檢測】** 頁籤完成檢測，平台將自動根據您的作答結果為您調配最佳補強教材！")
    else:
        quiz = st.session_state.quiz_data
        u_ans = st.session_state.user_answers
        
        score = sum(1 for i, q in enumerate(quiz["mcq"]) if u_ans["mcq"][i] == q["options"][q["correct_index"]])
        total = len(quiz["mcq"])
        pct = (score / total) * 100
        weak_tags = [q.get("concept_tag", "核心觀念") for i, q in enumerate(quiz["mcq"]) if u_ans["mcq"][i] != q["options"][q["correct_index"]]]
        
        if pct >= 80:
            mastery_level = "🟢 精熟級"
        elif pct >= 60:
            mastery_level = "🟡 基礎級"
        else:
            mastery_level = "🔴 待加強"

        st.markdown(f"""
        <div class="civics-card">
            <h4>🎯 您的精熟程度診斷：<span style="color: #38bdf8;">{mastery_level}</span> (得分 {score}/{total})</h4>
            <p>需補強之重點標籤：<b>{', '.join(weak_tags) if weak_tags else '無（觀念掌握良好）'}</b></p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🪄 生成/更新濃縮摘要、心智圖與補強講義", type="primary"):
            with st.spinner("AI 正在根據您的診斷結果提煉濃縮摘要、心智圖與專屬補強講義..."):
                text_content = materials[selected_topic]
                remedial_text = generate_remedial_material(selected_topic, text_content, mastery_level, weak_tags)
                st.session_state["remedial_" + selected_topic] = remedial_text
                logger_utils.log_remedial_view(prof, selected_topic, mastery_level)

        if "remedial_" + selected_topic in st.session_state:
            st.success("✨ **專屬適性濃縮摘要、觀念心智圖與補強講義**")
            st.markdown(st.session_state["remedial_" + selected_topic])

    st.markdown("---")
    st.markdown("#### 📜 課本原文講義參考 (高對比閱讀視窗)")
    text_content = materials[selected_topic]
    safe_html_content = html.escape(text_content)
    st.markdown(f'<div class="reader-container">{safe_html_content}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 3：公民 AI 素養問答小助手 (Q&A Assistant)
# ══════════════════════════════════════════════
with tab3:
    st.markdown("### 💡 公民 AI 素養問答小助手")
    st.caption("閱讀講義或做完檢測還有不理解的地方嗎？輸入問題，AI 老師用生活實例解惑！")

    q_input = st.text_input("💬 請輸入你的問題（例如：什麼是位階？為什麼憲法效力最高？）：")
    
    if st.button("❓ 請 AI 老師解答", type="primary"):
        if q_input.strip():
            with st.spinner("AI 老師思考中，正在為你準備易懂的回答..."):
                topic_text = materials[selected_topic]
                answer = ask_civics_ai(q_input, selected_topic, topic_text, student_level=res['level_name'])
                st.session_state.chat_history.append((q_input, answer))
                logger_utils.log_ai_chat(prof, q_input, answer)
        else:
            st.warning("請先輸入問題喔！")

    if st.session_state.chat_history:
        st.markdown("---")
        st.markdown("#### 📜 問答紀錄")
        for q, a in reversed(st.session_state.chat_history):
            with st.chat_message("user"):
                st.write(q)
            with st.chat_message("assistant", avatar="🏛️"):
                st.markdown(a)

# ══════════════════════════════════════════════
# TAB 4：👨‍🏫 教師學習歷程後台 (Teacher Analytics)
# ══════════════════════════════════════════════
with tab4:
    st.markdown("### 👨‍🏫 教師管理後台 — 全班學習歷程與精熟診斷看板")
    st.caption("老師只需在後台 materials/ 放課本講義，學生完成自主檢測後，即可在此隨時查閱精熟狀態與下載 Excel/CSV 報表。")

    # 全班總覽表格
    st.markdown("#### 📊 全班學生學習總覽清單")
    df_report = logger_utils.generate_csv_report()
    
    if df_report.empty:
        st.info("📭 目前尚無學生學習紀錄。當學生完成自主檢測時，數據將自動在此呈現。")
    else:
        st.dataframe(df_report, use_container_width=True)
        
        csv_bytes = df_report.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="📥 匯出全班學習歷程與精熟度 CSV 報表 (Excel 格式)",
            data=csv_bytes,
            file_name="8年級公民學習歷程與精熟診斷報表.csv",
            mime="text/csv",
            type="primary"
        )

    st.markdown("---")
    st.markdown("#### 👤 個別學生詳細學習歷程調閱器")
    
    all_records = logger_utils.get_all_student_records()
    if not all_records:
        st.info("尚無學生歷程檔案。")
    else:
        student_options = []
        record_map = {}
        for r in all_records:
            s_info = r.get("student_info", {})
            label = f"{s_info.get('class_name','')} 班 {s_info.get('seat_num','')} 號 — {s_info.get('name','')}"
            student_options.append(label)
            record_map[label] = r
            
        selected_student_label = st.selectbox("請選擇欲調閱的學生檔案", sorted(student_options))
        selected_record = record_map.get(selected_student_label)
        
        if selected_record:
            s_info = selected_record.get("student_info", {})
            s_diag = selected_record.get("diagnostic") or {}
            s_tests = selected_record.get("mastery_tests", [])
            s_chats = selected_record.get("ai_chats", [])
            s_remedials = selected_record.get("remedial_views", [])
            
            c_a, c_b, c_c = st.columns(3)
            c_a.metric("👤 學生姓名", f"{s_info.get('name','')}")
            c_b.metric("🎯 起點前測得分", f"{s_diag.get('score','0')} / 5 題")
            c_c.metric("🎓 起點評定等級", f"{s_diag.get('level_name','未診斷')}")

            t_sub1, t_sub2, t_sub3 = st.tabs(["🎯 單元精熟檢測紀錄", "📚 補強講義閱讀紀錄", "💬 AI 問答歷程"])
            
            with t_sub1:
                if not s_tests:
                    st.info("該生尚無單元自主檢測紀錄。")
                else:
                    for i, q_rec in enumerate(reversed(s_tests)):
                        with st.expander(f"檢測紀錄 #{len(s_tests)-i} — {q_rec.get('topic','')} ({q_rec.get('timestamp','')})"):
                            st.write(f"**精熟等級**：`{q_rec.get('mastery_level','')}`｜得分：`{q_rec.get('score',0)} / {q_rec.get('total',0)}`")
                            st.write(f"**需補強考點標籤**：`{', '.join(q_rec.get('weak_tags',[])) if q_rec.get('weak_tags') else '無'}`")
                            sa_list = q_rec.get("sa_responses", [])
                            if sa_list:
                                st.markdown("**簡答題回答與 AI 評語：**")
                                for sa_item in sa_list:
                                    st.markdown(f"- **題目**：{sa_item.get('question','')}")
                                    st.markdown(f"  - **回答**：{sa_item.get('answer','')}")
                                    st.markdown(f"  - **AI 評語**：{sa_item.get('feedback','')}")
            
            with t_sub2:
                if not s_remedials:
                    st.info("該生尚無適性補強講義閱讀紀錄。")
                else:
                    for i, r_rec in enumerate(reversed(s_remedials)):
                        st.markdown(f"- **[{r_rec.get('timestamp','')}]** 研讀單元：`{r_rec.get('topic','')}` (層級：`{r_rec.get('level','')}`)")
            
            with t_sub3:
                if not s_chats:
                    st.info("該生尚無 AI 提問紀錄。")
                else:
                    for c_rec in reversed(s_chats):
                        st.markdown(f"**[{c_rec.get('timestamp','')}] 問：** {c_rec.get('question','')}")
                        st.info(f"**AI 答：** {c_rec.get('answer','')}")

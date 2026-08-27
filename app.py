import streamlit as st
import unit_manager
import logger_utils
import data_loader
import os
import json
import html
from dotenv import load_dotenv

# --- Page Config ---
st.set_page_config(
    page_title="國中八年級公民 AI 智慧學習館",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_dotenv()

# --- Custom High-Contrast Modern Theme ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Noto Sans TC', -apple-system, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #090d16 0%, #0f172a 50%, #1e1b4b 100%);
        color: #f8fafc !important;
    }
    
    .stMarkdown p, .stMarkdown span, .stMarkdown strong, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #f8fafc !important;
    }
    
    /* Header Banner */
    .app-header {
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.4) 0%, rgba(147, 51, 234, 0.35) 50%, rgba(236, 72, 153, 0.25) 100%);
        backdrop-filter: blur(16px);
        border: 1.5px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 1.8rem 2.2rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
    }
    
    .app-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    
    .app-subtitle {
        font-size: 1.05rem;
        color: #cbd5e1 !important;
        font-weight: 500;
    }

    /* Cards */
    .feature-card {
        background: rgba(30, 41, 59, 0.85);
        border: 1.5px solid #334155;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }

    .key-point-card {
        background: rgba(15, 23, 42, 0.75);
        border-left: 5px solid #818cf8;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        font-size: 1.05rem;
        line-height: 1.6;
    }

    .case-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(49, 46, 129, 0.4) 100%);
        border: 1.5px solid #6366f1;
        border-radius: 16px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
    }

    .remedial-box {
        background: linear-gradient(135deg, rgba(234, 88, 12, 0.15) 0%, rgba(30, 41, 59, 0.9) 100%);
        border: 2px solid #f97316;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.2rem 0;
    }

    .summary-metric-card {
        background: rgba(30, 41, 59, 0.9);
        border: 1.5px solid #475569;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    }

    /* Tabs Styling */
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
        padding: 0.75rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }

    div[data-testid="stTabs"] button p,
    div[data-testid="stTabs"] button span,
    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] span {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
    }

    div[data-testid="stTabs"] button[aria-selected="true"],
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%) !important;
        border: 2px solid #818cf8 !important;
        border-bottom: 4px solid #fef08a !important;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] p,
    div[data-testid="stTabs"] button[aria-selected="true"] span {
        color: #fef08a !important;
        -webkit-text-fill-color: #fef08a !important;
        font-weight: 800 !important;
    }

    .badge-status-mastered {
        background: rgba(34, 197, 94, 0.2);
        border: 1.5px solid #22c55e;
        color: #4ade80 !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }

    .badge-status-practice {
        background: rgba(234, 179, 8, 0.2);
        border: 1.5px solid #eab308;
        color: #facc15 !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }

    .badge-status-look {
        background: rgba(239, 68, 68, 0.2);
        border: 1.5px solid #ef4444;
        color: #f87171 !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }

    .reader-container {
        background-color: #0b1120 !important;
        color: #ffffff !important;
        padding: 1.8rem;
        border-radius: 12px;
        border: 1.5px solid #334155;
        font-size: 1.05rem;
        line-height: 1.85;
        max-height: 450px;
        overflow-y: auto;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "user_role" not in st.session_state:
    st.session_state.user_role = "student"  # "student" or "teacher"
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

# Load all units
all_units = unit_manager.load_all_units()
if not all_units:
    st.error("⚠️ 尚未載入任何學習單元，請由教師端新增教材。")
    st.stop()

# --- Sidebar: Role & Student / Navigation ---
with st.sidebar:
    st.markdown("### 🏛️ 身分切換")
    role_choice = st.radio(
        "選擇操作身分",
        ["🎓 我是學生", "👨‍🏫 我是老師"],
        index=0 if st.session_state.user_role == "student" else 1,
        label_visibility="collapsed"
    )
    new_role = "teacher" if "老師" in role_choice else "student"
    if new_role != st.session_state.user_role:
        st.session_state.user_role = new_role
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
        
        entered_name = st.text_input("姓名", value=st.session_state.student_name, placeholder="例如：王小明")
        st.session_state.student_class = selected_class
        st.session_state.student_seat = selected_seat
        st.session_state.student_name = entered_name.strip()

        st.markdown("---")
        st.markdown("### 📚 選擇學習單元")
        unit_titles = [u["title"] for u in all_units]
        
        # Ensure default unit id is set
        if st.session_state.current_unit_id is None and all_units:
            st.session_state.current_unit_id = all_units[0]["id"]
            
        cur_unit = unit_manager.get_unit(st.session_state.current_unit_id) or all_units[0]
        cur_idx = unit_titles.index(cur_unit["title"]) if cur_unit["title"] in unit_titles else 0
        
        selected_title = st.selectbox("選擇學習單元", unit_titles, index=cur_idx, label_visibility="collapsed")
        
        # Check if changed
        for u in all_units:
            if u["title"] == selected_title and u["id"] != st.session_state.current_unit_id:
                st.session_state.current_unit_id = u["id"]
                st.session_state.practice_submitted = False
                st.session_state.practice_answers = {}
                st.session_state.chat_history = []
                st.rerun()

    else:
        st.markdown("### 👨‍🏫 教師管理功能")
        st.info("教師只需新增教材與貼上課本內容，AI 自動為您萃取重點、生活案例、題目與補救指引！")

# ══════════════════════════════════════════════
# 🎓 學生端 (Student Portal)
# ══════════════════════════════════════════════
if st.session_state.user_role == "student":
    student_info = {
        "class_name": st.session_state.student_class,
        "seat_num": st.session_state.student_seat,
        "name": st.session_state.student_name or "同學"
    }

    current_unit = unit_manager.get_unit(st.session_state.current_unit_id) or all_units[0]

    # Top Banner
    st.markdown(f"""
    <div class="app-header">
        <div class="app-title">🏛️ 國中公民 AI 智慧自主學習館</div>
        <div class="app-subtitle">輕鬆閱讀重點與生活實例 · 小試身手了解學習成效 · AI 助教陪伴自主成長</div>
        <div style="margin-top: 1rem;">
            <span style="background: rgba(99, 102, 241, 0.35); border: 1.5px solid #818cf8; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-weight: 700; margin-right: 8px;">
                👤 {student_info['class_name']} 班 {student_info['seat_num']} 號 {student_info['name']}
            </span>
            <span style="background: rgba(168, 85, 247, 0.35); border: 1.5px solid #c084fc; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-weight: 700;">
                📖 當前單元：{current_unit['title']}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Three Student Tabs
    tab_learn, tab_practice, tab_footprint = st.tabs([
        "📖 開始學習",
        "✏️ 小試身手",
        "🌱 我的足跡"
    ])

    # ──────────────────────────────────────────────
    # 1. 📖 開始學習 (Learn)
    # ──────────────────────────────────────────────
    with tab_learn:
        st.markdown(f"### 📖 {current_unit['title']} — 重點與生活實例")

        # 核心學習重點
        key_points = current_unit.get("key_points", [])
        if key_points:
            st.markdown("#### 📌 核心學習重點")
            for idx, pt in enumerate(key_points):
                st.markdown(f'<div class="key-point-card"><b>重點 {idx+1}：</b> {pt}</div>', unsafe_allow_html=True)

        # 國中生白話整理
        easy_content = current_unit.get("easy_content", "")
        if easy_content:
            st.markdown("---")
            st.markdown("#### 🌟 輕鬆看懂這堂課")
            st.markdown(f'<div class="feature-card">{easy_content}</div>', unsafe_allow_html=True)

        # 生活化情境案例
        life_cases = current_unit.get("life_cases", [])
        if life_cases:
            st.markdown("---")
            st.markdown("#### 🏫 生活與校園情境案例")
            for c in life_cases:
                st.markdown(f"""
                <div class="case-card">
                    <h4 style="color: #93c5fd; margin-bottom: 0.5rem;">{c.get('title','情境實例')}</h4>
                    <p style="font-size: 1.05rem; line-height: 1.7; color: #f1f5f9;">{c.get('story','')}</p>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.8rem 1.2rem; border-radius: 8px; font-weight: 700; color: #fef08a; border-left: 4px solid #facc15; margin-top: 0.8rem;">
                        {c.get('takeaway','')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # 觀念心智圖
        mindmap_mermaid = current_unit.get("mindmap_mermaid", "")
        if mindmap_mermaid:
            st.markdown("---")
            st.markdown("#### 🧠 核心觀念心智圖")
            st.markdown(f"```mermaid\n{mindmap_mermaid}\n```")

        # 課本原文閱讀 (可摺疊)
        raw_text = current_unit.get("raw_content", "")
        if raw_text:
            with st.expander("📜 查看課本講義原文對照 (點擊展開/收合)"):
                safe_html = html.escape(raw_text)
                st.markdown(f'<div class="reader-container">{safe_html}</div>', unsafe_allow_html=True)

        st.info("💡 讀完重點與生活案例了嗎？切換至 **【✏️ 小試身手】** 進行簡單的觀念練習吧！")

    # ──────────────────────────────────────────────
    # 2. ✏️ 小試身手 (Practice)
    # ──────────────────────────────────────────────
    with tab_practice:
        st.markdown(f"### ✏️ 小試身手 — {current_unit['title']}")
        st.caption("簡單完成幾道生活化概念練習，了解自己掌握了哪些重點！")

        questions = current_unit.get("practice_questions", [])
        remedy_guides = current_unit.get("remediation_guides", {})

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
                        key=f"p_q_{current_unit['id']}_{i}",
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

                if st.button("🔄 重新小試身手"):
                    st.session_state.practice_submitted = False
                    st.session_state.practice_answers = {}
                    st.rerun()

        # 隨身 AI 助教
        st.markdown("---")
        st.markdown("#### 💬 公民 AI 助教隨身問")
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
            st.markdown("##### 📜 問答交流紀錄")
            for q_text, a_text in reversed(st.session_state.chat_history):
                with st.chat_message("user"):
                    st.write(q_text)
                with st.chat_message("assistant", avatar="🏛️"):
                    st.markdown(a_text)

    # ──────────────────────────────────────────────
    # 3. 🌱 我的足跡 (Footprint)
    # ──────────────────────────────────────────────
    with tab_footprint:
        st.markdown("### 🌱 我的自主學習足跡")
        st.caption("記錄你在每個學習單元的成長歷程。按照自己的節奏學習，每一步都是進步！")

        footprints = logger_utils.get_student_footprint(student_info)
        
        if not footprints:
            st.info("🌱 你尚未在任何單元進行「小試身手」。快挑選一個單元開始學習吧！")
        else:
            col_stat1, col_stat2 = st.columns(2)
            with col_stat1:
                st.metric("已完成學習單元", f"{len(footprints)} 個單元")
            with col_stat2:
                mastered_count = sum(1 for f in footprints if "🌳" in f.get("status", ""))
                st.metric("已完全掌握單元", f"{mastered_count} 個單元")

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
                        <h4 style="margin: 0; color: #a5b4fc;">{fp.get('unit_title','')}</h4>
                        <span class="{badge_class}">{status_str}</span>
                    </div>
                    <p style="margin: 0.3rem 0; color: #cbd5e1;"><b>🔄 練習次數：</b>{fp.get('practice_count',1)} 次 ｜ <b>重點概念：</b>{weak_text}</p>
                    <p style="margin: 0.3rem 0; font-size: 0.9rem; color: #94a3b8;">最後學習時間：{fp.get('last_updated','')}</p>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 👨‍🏫 教師端 (Teacher Portal)
# ══════════════════════════════════════════════
else:
    st.markdown("""
    <div class="app-header">
        <div class="app-title">👨‍🏫 教師管理中心 — 學習單元與學生學習狀況</div>
        <div class="app-subtitle">輕鬆新增教材與課本內容 · 系統自動建立重點、生活實例與題目 · 掌握全班學習摘要</div>
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
        st.caption("教師只需輸入名稱與貼上課本內容，系統將自動萃取重點、整理白話內容、建立生活案例、題目與補救說明。")

        # ➕ 新增教材區
        with st.expander("➕ 新增學習單元 (點擊展開新增)", expanded=False):
            with st.form("new_unit_form"):
                st.markdown("#### 步驟 1：輸入單元名稱")
                new_title = st.text_input("單元名稱", placeholder="例如：第3課：政府的組織與職權")
                
                st.markdown("#### 步驟 2：貼上教材內容")
                new_content = st.text_area("課本教材內容", placeholder="請直接貼上課本段落、講義文字或重點內容...", height=220)
                
                st.markdown("#### 步驟 3：按下按鈕")
                submit_create = st.form_submit_button("🚀 建立學習單元", type="primary")
                
                if submit_create:
                    if not new_title.strip() or not new_content.strip():
                        st.warning("請填寫單元名稱與教材內容喔！")
                    else:
                        with st.spinner("🤖 AI 正在分析教材、萃取重點、建立生活案例與練習題..."):
                            created = unit_manager.create_unit(new_title.strip(), new_content.strip())
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
                            <span style="font-size: 0.9rem; color: #94a3b8;">更新時間：{u.get('updated_at', u.get('created_at',''))}</span>
                        </div>
                        <p style="margin-top: 0.5rem; color: #cbd5e1;">
                            <b>📌 萃取重點：</b>{len(u_kps)} 條 ｜ <b>✏️ 小試身手：</b>{len(u_qs)} 題 ｜ <b>🏫 生活案例：</b>{len(u.get('life_cases',[]))} 個
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
                        st.markdown(f"##### ✏️ 小試身手練習題 ({len(u_qs)} 題)：")
                        for idx, q in enumerate(u_qs):
                            st.markdown(f"**第 {idx+1} 題【{q.get('concept_tag','')}】**：{q.get('question','')}")
                            st.caption(f"選項：{', '.join(q.get('options',[]))}｜正確答案：選項 {q.get('correct_index',0)+1}")
                        st.markdown("---")

                    # 修改教材展開
                    if st.session_state.get(f"show_edit_{u_id}", False):
                        with st.form(f"edit_form_{u_id}"):
                            edit_t = st.text_input("修改單元名稱", value=u_title)
                            edit_c = st.text_area("修改教材內容", value=u.get("raw_content",""), height=180)
                            regen = st.checkbox("🔄 是否由 AI 重新自動生成重點、案例與題目？", value=False)
                            save_edit = st.form_submit_button("💾 儲存修改", type="primary")
                            if save_edit:
                                unit_manager.update_unit(u_id, edit_t, edit_c, regenerate=regen)
                                st.session_state[f"show_edit_{u_id}"] = False
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
                <div style="font-size: 1.1rem; color: #cbd5e1; margin-bottom: 0.3rem;">📅 今日學習進度</div>
                <div style="font-size: 2rem; font-weight: 800; color: #4ade80;">
                    今天有 {summary['completed_today_count']} 位學生完成學習
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c_sum2:
            attention_color = "#f87171" if summary['need_attention_count'] > 0 else "#94a3b8"
            st.markdown(f"""
            <div class="summary-metric-card" style="border-left: 5px solid {attention_color};">
                <div style="font-size: 1.1rem; color: #cbd5e1; margin-bottom: 0.3rem;">💡 教學關懷提醒</div>
                <div style="font-size: 2rem; font-weight: 800; color: {attention_color};">
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

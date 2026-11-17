# 📑 CivilEdu_AI — 2026-11-17 本日完整開發紀錄檔 (Development Log)

**專案名稱**：CivilEdu_AI 國中公民思辨星系 ｜ AI 智慧自主學習館  
**開發日期**：2026-11-17  
**核心主題**：學生端姓名免填隱私化、身分選擇浮動視窗化（Modal Dialog）、主頁頂部單元選擇控制列、首頁視野完全釋放與即刻啟航機制  
**版本標籤**：`2026-11-17-v1` (階段 32)  

---

## 🎯 一、 今日開發里程碑總覽 (Milestones Summary)

| 項目 | 核心技術與成果摘要 | 影響檔案 |
| :--- | :--- | :--- |
| **學生免填姓名** | 移除學生基本資料中的「姓名」輸入欄位，僅保留「班級」與「座號」下拉選單；保護校園學生隱私，免去手機/平板鍵盤輸入摩擦。 | [`app.py`](file:///C:/Users/awen8/CivilEdu_AI/app.py)<br>[`logger_utils.py`](file:///C:/Users/awen8/CivilEdu_AI/logger_utils.py) |
| **身分選擇浮動視窗化** | 將身分切換改為 `@st.dialog` 原生浮動視窗，登入時自動彈出；整合學生與教師分頁，側邊欄預設收合不佔據首頁空間。 | [`app.py`](file:///C:/Users/awen8/CivilEdu_AI/app.py) |
| **主頁頂部單元控制列** | 將「📚 選擇學習單元」由側邊欄移至主頁面正上方，搭配「🏛️ 切換身分」快速按鈕，直覺切換學習單元。 | [`app.py`](file:///C:/Users/awen8/CivilEdu_AI/app.py) |
| **完成選定即刻啟航** | 學生確認身分後自動載入預設單元，直接開啟完整學習頁面（含四大模組分頁），不再停滯於導引提示畫面。 | [`app.py`](file:///C:/Users/awen8/CivilEdu_AI/app.py)<br>[`README.md`](file:///C:/Users/awen8/CivilEdu_AI/README.md) |
| **歷程鍵值向後相容** | 調整 `get_student_key` 格式為 `班級_座號`，並在 `load_student_record` 內建歷史紀錄相容機制，舊生作答足跡完全不流失。 | [`logger_utils.py`](file:///C:/Users/awen8/CivilEdu_AI/logger_utils.py) |

---

## 🛠️ 二、 詳細架構調整

### 1. 浮動視窗設計 (`identity_dialog`)
- 使用 Streamlit `@st.dialog` 封裝，登入時自動偵測 `show_identity_dialog` 彈出。
- 內建 `st.tabs(["🎓 我是學生", "👨‍🏫 我是老師"])`：
  - **學生分頁**：班級（801~821）、座號（01~30）雙欄下拉選單，點選「🚀 確認身分並開啟學習頁面」一鍵啟航。
  - **教師分頁**：專屬管理密碼驗證，通過後直接進入觀測中心。

### 2. 首頁與頂部佈局優化
- 側邊欄設定 `initial_sidebar_state="collapsed"`，首頁全寬呈現，視野開闊。
- 主學習區頂端配置 `col_unit_sel, col_switch_btn = st.columns([4, 1.2])`，清晰切換課程進度。

---

## 🧪 三、 自動化驗證成果

- **語法編譯**：`app.py`、`logger_utils.py` AST 語法檢查 100% 通過。
- **Streamlit AppTest 測試**：
  1. 初始啟動自動彈出身分浮動視窗。
  2. 學生身分確認後直接開啟 4 大核心分頁（`📖 開始學習`、`✏️ 小試身手`、`💬 問問AI助教`、`🌱 我的足跡`）。
  3. 主頁面頂部單元選擇器順暢切換單元。
  4. 點擊「切換身分」重新喚起彈窗，切換教師密碼驗證無縫進入教師後台。

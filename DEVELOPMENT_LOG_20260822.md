# 📑 Exam_TutorAI — 2026-08-22 開發紀錄檔 (Development Log)

**專案名稱**：CivilEdu_AI / Exam_TutorAI 國中八年級公民 AI 智慧學習平台  
**開發日期**：2026-08-22  
**開發重點**：講義重點濃縮摘要、Mermaid 視覺化心智圖、Portable Git 環境維護、GitHub 專案同步與雲端部署配置  

---

## 🎯 一、 今日開發亮點總覽 (Key Highlights)

1. **📚 課本講義重點摘要與視覺化心智圖 (Summary & Mind Map)**：
   - 在 **【📚 精熟診斷與適性補強教材】** 頁面中，新增獨立 AI 生成引擎 `generate_summary_and_mindmap()`。
   - 無需先進行測驗，點擊「🪄 一鍵生成講義摘要與觀念心智圖」即可直接從講義原文產出：
     - **📌 1 分鐘重點濃縮摘要 (Executive Summary)**：核心概念速記與觀念避坑卡片（附判斷口訣）。
     - **🧠 視覺化觀念結構心智圖 (Mermaid Concept Mind Map)**：自動輸出標準 `graph TD` Mermaid 語法，在 Streamlit 中直接渲染成樹狀結構心智圖。

2. **🛠️ 頁面架構重構 (Sub-Tabs Redesign)**：
   - 將 **【📚 精熟診斷與適性補強教材】** 頁面拆分為雙子頁籤：
     - `子頁籤 1：🧠 課本講義摘要與觀念心智圖`（無前置門檻，隨時預習/複習）
     - `子頁籤 2：🎯 個人化弱點診斷與適性補強`（結合前測/單元檢測評定結果進行適性補強）

3. **📦 Portable Git 免安裝環境整合與 Git Commit**：
   - 下載並配置可攜式 MinGit (`git version 2.44.0.windows.1`)。
   - 精確優化 `.gitignore`，過濾 PDFs、暫存文件與二進位檔案，保持版本庫輕量與資安合規。
   - 連結 GitHub 遠端儲存庫：`https://github.com/SevynLee777/CivilEdu_AI.git`。

4. **☁️ 雲端部署最佳化與 Secrets 金鑰配置 (.streamlit/config.toml)**：
   - 建立 `.streamlit/config.toml` 主題與伺服器設定，支援暗黑模式美學與行動端響應式排版。
   - 提供 Streamlit Community Cloud (0 元免費雲端) 完整部署步驟指引與 Gemini API Key secrets 設定說明。

---

## 🛠️ 二、 詳細修訂檔案與程式碼對照

### 1. `app.py`
- **新增函式**：`generate_summary_and_mindmap(topic_name, topic_text)`
  - Prompt 規範 Gemini 生成 📌 濃縮摘要（核心速記、避坑卡片）與 🧠 Mermaid 心智圖 (`graph TD`)。
- **重構 Tab 2 介面**：導入 `st.tabs(["🧠 課本講義摘要與觀念心智圖", "🎯 個人化弱點診斷與適性補強"])`。

### 2. `.gitignore`
- 允許 `.streamlit/config.toml` 納入版本控制，同時忽略 `.streamlit/secrets.toml`。
- 排除 `archive_tools/downloaded_pdfs/`、`archive_tools/temp_docs/`、`student_logs/`、`backups/` 與 `*.zip`。

### 3. `.streamlit/config.toml`
- 配置 Streamlit 主題配色（`#38bdf8` 蔚藍主色、`#0f172a` 深海藍背景、高對比白字）。

---

## 📝 三、 Git 提交紀錄 (Commit History)

| Commit Hash | 提交訊息 (Commit Message) |
| :--- | :--- |
| `d0f23bc` | `feat: Add direct lecture summary and Mermaid mind map generator to Tab 2` |
| `86352cc` | `config: Add Streamlit cloud theme and server configuration` |
| `fce8360` | `feat: Add condensed summary and Mermaid mind map to adaptive remediation material` |
| `3e02a9e` | `Update default question count options to 4, 8, 12 in app.py` |

---

## 🚀 四、 本地啟動與雲端部署操作指引

### 1. 本地啟動指令：
```powershell
cd C:\Users\awen8\Exam_TutorAI
.\run.bat
```
*(或在 PowerShell 執行 `python -m streamlit run app.py`)*

### 2. 推送至 GitHub 指令：
```powershell
cd C:\Users\awen8\Exam_TutorAI; & "C:\Users\awen8\git-portable\cmd\git.exe" push origin main
```

### 3. Streamlit Cloud 雲端部署 (免費 0 元)：
1. 登入 [share.streamlit.io](https://share.streamlit.io/) 連結 GitHub 帳號。
2. 選擇 Repository: `SevynLee777/CivilEdu_AI`，Branch: `main`，Main file: `app.py`。
3. Secrets 貼上 API Key：
   ```toml
   GEMINI_API_KEY = "your_gemini_api_key_here"
   ```
4. 點擊 **Deploy** 完成上線。

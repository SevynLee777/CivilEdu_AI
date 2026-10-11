# 🌌 公民思辨星系 ｜ 國中八年級公民自主學習平台 (CivilEdu_AI)

本專案是專為**國中八年級公民科**打造的沉浸式 AI 智慧自主學習系統。平台融合**新世代生成式 AI（Google GenAI 2.5 Flash）**、**八年級素養教材庫**、**生活化情境案例**與**個人化自主學習歷程日誌**，兼顧學生自主探索與教師後台督導。

---

## 🧭 系統分析與核心架構

### 1. 核心角色與權限架構
- **未就緒 / 訪客**：初次訪問網站時，主畫面啟動「航行準備中」防禦機制，提供動態即時檢核看板與星系特色導覽，防止未登記直接作答。
- **學生端 (Student)**：完成身分、班級、座號、姓名登記並選定學習單元後，解鎖頂部銀河個人學習儀表板與四大核心模組：
  1. **📖 開始學習**：白話生活化手札重點、生活實例、直式樹狀心智圖（Mermaid `graph LR`）、一鍵直達練習按鈕。
  2. **✏️ 小試身手**：8 題生活情境素養題、即時批改評分、觀念充電站補強指南。
  3. **💬 問問AI助教**：蘇格拉底式引導問答、推薦思辨啟發題。
  4. **🌱 我的足跡**：自主學習歷程統計、答題完成度與錯題診斷分析。
- **教師端 (Teacher)**：需通過專屬密碼驗證視窗（Modal Dialog），進入教師管理後台：
  - 教材單元管理（AI 自動生成 8 題素養題目、情境案例與心智圖、手動編修與刪除）。
  - 全班學習歷程看板（各班作答率、平均分、錯題排行、學生個人足跡追蹤）。
  - 報表匯出（下載 CSV / JSON 學習歷程數據）。

### 2. 四條件啟航防禦機制（Gatekeeper Mechanism）
為確保自主學習歷程之真實性與完整歸檔，系統設有動態載入防禦門檻：
$$\text{Ready 門檻} = (\text{身分} == \text{學生}) \land (\text{姓名非空}) \land (\text{學習單元已選定})$$
- **未就緒**：即時展示 4 步驟動態檢核看板（已完成步驟顯示 ✅，未完成顯示 ⏳）與四大特色卡片。
- **滿足條件**：即刻動態渲染個人學習看板與四大標籤頁。

---

## 📊 網站流程設計圖 (Website Process Flowchart)

為了讓圖表文字清楚易讀，流程圖拆成三張：**① 系統總覽** → **② 學生學習流程** → **③ 教師管理流程**。

### ① 系統總覽

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'18px', 'primaryColor':'#E0F2FE', 'primaryBorderColor':'#0284C7', 'primaryTextColor':'#0F172A', 'lineColor':'#475569'}}}%%
flowchart LR
    classDef role fill:#1E3A8A,stroke:#1E3A8A,color:#FFFFFF;
    classDef data fill:#DCFCE7,stroke:#16A34A,color:#14532D;
    classDef ai fill:#FEF3C7,stroke:#D97706,color:#78350F;

    U([使用者]) --> R{選擇身分}
    R -->|🎓 學生| S[學生端<br/>四大學習模組]:::role
    R -->|👨‍🏫 老師| T[教師後台<br/>密碼驗證]:::role

    S -->|讀取教材| D[(教材庫<br/>units_db.json)]:::data
    S <-->|寫入 / 查詢歷程| L[(學習歷程<br/>student_logs)]:::data
    T <-->|管理單元| D
    T -->|全班分析| L

    S -.->|AI 助教問答| G[[Gemini 2.5 Flash]]:::ai
    T -.->|AI 生成教材| G
```

### ② 學生學習流程

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'18px', 'primaryColor':'#E0F2FE', 'primaryBorderColor':'#0284C7', 'primaryTextColor':'#0F172A', 'lineColor':'#475569'}}}%%
flowchart TD
    classDef guard fill:#FFEDD5,stroke:#EA580C,color:#7C2D12;
    classDef tab fill:#1E3A8A,stroke:#1E3A8A,color:#FFFFFF;
    classDef data fill:#DCFCE7,stroke:#16A34A,color:#14532D;
    classDef ai fill:#FEF3C7,stroke:#D97706,color:#78350F;

    A[填寫個人資料<br/>選擇學習單元] --> B{資料齊全？}
    B -->|否| W[航行準備中<br/>提示缺漏項目]:::guard
    W --> A
    B -->|是| C[學習儀表板]

    C --> T1[📖 開始學習]:::tab
    C --> T2[✏️ 小試身手]:::tab
    C --> T3[💬 AI 助教]:::tab
    C --> T4[🌱 我的足跡]:::tab

    T1 -->|前往練習| T2
    T2 --> Q[8 題自動批改<br/>觀念補強]
    Q -->|寫入| L[(學習歷程<br/>student_logs)]:::data
    T3 --> G[Gemini<br/>引導式回覆]:::ai
    T4 -.->|讀取| L
```

### ③ 教師管理流程

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'18px', 'primaryColor':'#E0F2FE', 'primaryBorderColor':'#0284C7', 'primaryTextColor':'#0F172A', 'lineColor':'#475569'}}}%%
flowchart LR
    classDef dash fill:#1E3A8A,stroke:#1E3A8A,color:#FFFFFF;
    classDef guard fill:#FFEDD5,stroke:#EA580C,color:#7C2D12;

    A[選擇老師] --> B{已驗證？}
    B -->|否| P[輸入密碼]
    P -->|正確| D[教師儀表板]:::dash
    P -->|取消| H[返回首頁]:::guard
    B -->|是| D

    D --> M[單元管理<br/>編輯・AI 生成]
    D --> N[學生歷程看板]
    D --> E[報表匯出<br/>CSV / JSON]
    D --> O[登出] --> H
```

---

## 🛠️ 技術堆疊 (Tech Stack)

| 領域 | 技術 / 套件 | 說明 |
| :--- | :--- | :--- |
| **前端應用** | `streamlit` (>= 1.59.1) | 響應式 Web 框架，支援 `@react-aria/tabs` 標籤頁與 Session State 狀態機 |
| **樣式排版** | CSS3 (`clamp()` 流體字級) | 全載具響應式適配，保證手機、平板與桌面皆有舒適易讀的字型排版 |
| **AI 引擎** | `google-genai` (>= 2.28.0) | Google 官方新版 SDK，調用 `gemini-2.5-flash` 進行結構化教材生成與引導式問答 |
| **可視化圖表** | Mermaid (`graph LR`) | 呈現直式樹狀生活化公民思辨心智圖 |
| **歷程分析** | `pandas` | 學生個人足跡日誌處理、全班作答摘要統計與 CSV 匯出 |
| **資料持久化** | 本地 JSON 儲存庫 | `units_db.json`（教材庫）、`student_logs/*.json`（學習足跡） |

---

## 📂 專案檔案結構

```text
CivilEdu_AI/
├── app.py                      # 主應用程式（公民思辨星系 Streamlit 介面）
├── unit_manager.py             # 學習單元管理與 Google GenAI 生成引擎
├── logger_utils.py             # 學生歷程紀錄、統計與報表匯出模組
├── units_db.json               # 系統學習單元資料庫（含重點、案例、8題練習、心智圖）
├── config.json                 # 系統配置（科目名稱、AI 人設提示詞）
├── student_logs/               # 學生個人學習歷程 JSON 日誌目錄
├── requirements.txt            # Python 依賴清單
├── run.bat                     # Windows 快速啟動批次檔
├── README.md                   # 系統分析、架構說明與完整流程圖
└── DEVELOPMENT_LOG*.md         # 專案詳細開發與迭代歷程紀錄
```

---

## 🚀 快速啟動指引

### 1. 安裝環境依賴
```bash
pip install -r requirements.txt
```

### 2. 設定 Google Gemini API Key
可於系統環境變數或 `.streamlit/secrets.toml` 設定：
```bash
export GEMINI_API_KEY="您的_GEMINI_API_KEY"
```

### 3. 啟動應用程式
```bash
streamlit run app.py
```
或直接在 Windows 雙擊執行 `run.bat`。

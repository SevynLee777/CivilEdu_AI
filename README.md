# 🌌 公民思辨星系 ｜ 國中八年級公民自主學習平台 (CivilEdu_AI)

本專案是專為**國中八年級公民科**打造的沉浸式 AI 智慧自主學習系統。平台融合**新世代生成式 AI（Google GenAI 2.5 Flash）**、**八年級素養教材庫**、**生活化情境案例**與**個人化自主學習歷程日誌**，兼顧學生自主探索與教師後台督導。

---

## 🧭 系統分析與核心架構

### 1. 核心角色與權限架構
- **未就緒 / 訪客**：初次訪問網站時，主畫面啟動「航行準備中」防禦機制，提供動態即時檢核看板與星系特色導覽，防止未登記直接作答。
- **學生端 (Student)**：完成身分、班級、座號、姓名登記並選定學習單元後，解鎖頂部銀河個人學習儀表板與四大核心模組：
  1. **📖 開始學習**：白話生活化手札重點、生活實例、直式樹狀心智圖（Mermaid `graph LR`）、一鍵直達練習按鈕。
  2. **✏️ 小試身手**：8 題生活情境素養題、即時批改評分、觀念充電站補強指南。
  3. **💬 公民 AI 助教隨身問**：蘇格拉底式引導問答、推薦思辨啟發題。
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

## 📊 網站完整流程設計圖 (Website Process Flowchart)

以下流程圖完整呈現身分選擇、密碼安全驗證、動態防禦機制、四大模組學習及數據落盤流程：

```mermaid
flowchart TD
    %% 樣式設定
    classDef startNode fill:#1E3A8A,stroke:#60A5FA,stroke-width:2px,color:#FFFFFF;
    classDef decisionNode fill:#312E81,stroke:#F59E0B,stroke-width:2px,color:#FFFFFF;
    classDef pageNode fill:#0F172A,stroke:#38BDF8,stroke-width:2px,color:#FFFFFF;
    classDef actionNode fill:#1E293B,stroke:#94A3B8,stroke-width:1.5px,color:#FFFFFF;
    classDef guardNode fill:#451A03,stroke:#F97316,stroke-width:2px,color:#FFFFFF;
    classDef dataNode fill:#064E3B,stroke:#10B981,stroke-width:2px,color:#FFFFFF;

    subgraph SG_Entry ["🌐 進入系統與身分選擇"]
        Start(["使用者連線至網站 (app.py)"]):::startNode
        InitSession["初始化 Session 狀態<br/>(身分=none, 單元=None)"]:::actionNode
        SelectRole{"左側邊欄選擇身分"}:::decisionNode

        Start --> InitSession
        InitSession --> SelectRole
    end

    subgraph SG_Guard ["🚀 首頁啟航防禦機制"]
        ShowDefense["主畫面：航行準備中<br/>• 4步驟即時狀態檢核表<br/>• 四大模組特色導覽卡片"]:::guardNode
        CheckReady{"檢查啟航防禦條件：<br/>姓名非空 且 已選單元？"}:::decisionNode
        ResetRole["重置身分至未選擇 (none)"]:::actionNode

        SelectRole --> |"未選擇 (none)"| ShowDefense
        ResetRole --> ShowDefense
        CheckReady --> |"否 (條件未滿足)"| ShowDefense
    end

    subgraph SG_Teacher ["👨‍🏫 教師管理後台流程"]
        CheckTeacherAuth{"是否已驗證密碼？"}:::decisionNode
        TeacherDialog["彈出密碼驗證視窗<br/>(teacher_auth_dialog)"]:::actionNode
        CheckPwd{"驗證密碼"}:::decisionNode
        TeacherVerified["驗證成功<br/>(is_teacher_authenticated=True)"]:::actionNode
        TeacherDashboard["主畫面：👨‍🏫 教師管理儀表板"]:::pageNode
        T_Manage["單元管理<br/>(新增/編輯/刪除/AI生成)"]:::actionNode
        T_Analytics["學生歷程看板<br/>(全班統計/作答率/個別足跡)"]:::actionNode
        T_Export["報表匯出<br/>(下載 CSV / JSON 報表)"]:::actionNode
        T_Logout["登出管理端"]:::actionNode

        SelectRole --> |"👨‍🏫 我是老師"| CheckTeacherAuth
        CheckTeacherAuth --> |"未驗證"| TeacherDialog
        TeacherDialog --> CheckPwd
        CheckPwd --> |"密碼正確"| TeacherVerified
        CheckPwd --> |"取消或關閉"| ResetRole
        CheckTeacherAuth --> |"已驗證"| TeacherVerified
        TeacherVerified --> TeacherDashboard

        TeacherDashboard --> T_Manage
        TeacherDashboard --> T_Analytics
        TeacherDashboard --> T_Export
        TeacherDashboard --> T_Logout
        T_Logout --> ResetRole
    end

    subgraph SG_Student ["🎓 學生端自主學習流程"]
        StudentInput["側邊欄填寫資料：<br/>1. 班級 (801~821)<br/>2. 座號 (01~30)<br/>3. 輸入姓名<br/>4. 選擇學習單元"]:::actionNode
        StudentPortal["主畫面解鎖：<br/>1. 頂部銀河個人學習儀表板<br/>2. 四大模組經典標籤頁 (st.tabs)"]:::pageNode
        TabNav{"選擇標籤頁"}:::decisionNode

        SelectRole --> |"🎓 我是學生"| StudentInput
        StudentInput --> CheckReady
        CheckReady --> |"是 (條件已滿足)"| StudentPortal
        StudentPortal --> TabNav

        %% 模組 1
        TabLearn["【📖 開始學習】<br/>• 生活化白話重點手札<br/>• 生活情境核心案例解析<br/>• 直式樹狀心智圖 (graph LR)"]:::pageNode
        JumpBtn["點擊按鈕：<br/>🚀 前往【✏️ 小試身手】觀念練習"]:::actionNode

        TabNav --> |"📖 開始學習"| TabLearn
        TabLearn --> JumpBtn
        JumpBtn --> |"程式化切換分頁"| TabPractice

        %% 模組 2
        TabPractice["【✏️ 小試身手】<br/>• 8 題素養情境單選題"]:::pageNode
        QuizSubmit["學生作答並送出成果"]:::actionNode
        QuizGrade["系統即時自動批改：<br/>• 計算總分與對錯分析<br/>• 展開觀念充電站補強指南"]:::pageNode
        SaveLog["自動寫入歷程紀錄<br/>(logger_utils.py)"]:::actionNode

        TabNav --> |"✏️ 小試身手"| TabPractice
        TabPractice --> QuizSubmit
        QuizSubmit --> QuizGrade
        QuizGrade --> SaveLog

        %% 模組 3
        TabAI["【💬 公民 AI 助教隨身問】<br/>• 獨立思辨對話專區<br/>• 推薦提問引導思考"]:::pageNode
        SendPrompt["學生提問送出"]:::actionNode
        GeminiCall["Google GenAI API (gemini-2.5-flash)<br/>角色扮演：國中公民啟發式助教"]:::actionNode
        AIResponse["動態生成引導式回覆<br/>(引導反思而非直接給答案)"]:::pageNode

        TabNav --> |"💬 公民 AI 助教隨身問"| TabAI
        TabAI --> SendPrompt
        SendPrompt --> GeminiCall
        GeminiCall --> AIResponse

        %% 模組 4
        TabFootprint["【🌱 我的足跡】<br/>• 個人歷程儀表板<br/>• 單元完成度進度條<br/>• 歷史測驗得分與錯題診斷<br/>• 學習歷程時間軸"]:::pageNode

        TabNav --> |"🌱 我的足跡"| TabFootprint
    end

    subgraph SG_Data ["💾 系統資料持久層"]
        DB_Units[("教材庫<br/>(units_db.json)")]:::dataNode
        DB_Logs[("學生歷程庫<br/>(student_logs/*.json)")]:::dataNode
        GeminiService["Google GenAI 服務<br/>(Gemini 2.5 Flash)"]:::dataNode
    end

    %% 資料流跨層關聯
    T_Manage <--> DB_Units
    T_Manage -. "呼叫 AI 萃取生成教材" .-> GeminiService
    T_Analytics <--> DB_Logs
    SaveLog --> DB_Logs
    TabFootprint <--> DB_Logs
    GeminiCall -. "API 請求與串流回應" .-> GeminiService
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

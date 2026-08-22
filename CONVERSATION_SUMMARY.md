# 📑 Exam_TutorAI — 今日對話紀錄與開發摘要

**對話日期**：2026-07-19  
**專案名稱**：Exam_TutorAI 國中八年級公民 AI 智慧學習館  
**當前版本**：`11507版`  

---

## 📌 今日對話與需求處理總覽

| 序號 | 使用者需求 / 提問 | 系統處理與開發成果 | 對應檔案 |
| :---: | :--- | :--- | :--- |
| **1** | 更換教材為適合八年級生的公民類科教材，提供新前台 | 將 `materials.zip` 內 Word 二進位 `.doc` 檔自動轉譯為乾淨 `.docx`；更新設定檔與資料載入器，並重新設計全新前台介面。 | [config.json](file:///C:/Users/awen8/Exam_TutorAI/config.json)<br>[data_loader.py](file:///C:/Users/awen8/Exam_TutorAI/data_loader.py)<br>[materials/](file:///C:/Users/awen8/Exam_TutorAI/materials) |
| **2** | 修正生成測驗時發生的 404 模型退役錯誤 | 封裝 `call_gemini_api()` 函式，自動在 `gemini-3.5-flash``gemini-flash-latest`、`gemini-2.0-flash` 模型間自動無縫備援切換。 | [app.py](file:///C:/Users/awen8/Exam_TutorAI/app.py) |
| **3** | 解決講義全文內容對比性過弱、文字看不清的問題 | 重構前台 CSS，新增高對比閱讀視窗 `.reader-container`（採純黑藍背景 `#0f172a` 與高亮度白字 `#ffffff` 及 1.85 倍行高）。 | [app.py](file:///C:/Users/awen8/Exam_TutorAI/app.py) |
| **4** | 要求學生先填寫班級座號並進行起點前測，再提供適性學習 | 建立學生登錄與前測流程，評定 `Level A/B/C` 三大層級，並將起點程度動態帶入 AI 隨堂出題、簡答批改與隨問隨答。 | [app.py](file:///C:/Users/awen8/Exam_TutorAI/app.py) |
| **5** | 選擇【方案二】紀錄每位學生的學習歷程與提供查詢 | 開發 `logger_utils.py` 模組，於 `student_logs/` 為每生建立獨立 JSON 日誌；新增 Tab 5 教師後台，支援全班歷程檢視與匯出 UTF-8-BOM CSV 報表 (Excel 格式)。 | [logger_utils.py](file:///C:/Users/awen8/Exam_TutorAI/logger_utils.py)<br>[student_logs/](file:///C:/Users/awen8/Exam_TutorAI/student_logs) |
| **6** | 將第一步登記學生基本資料改為下拉式選單 | 班級設定為 `801` ~ `821` 下拉選單，座號設定為 `01` ~ `30` 下拉選單，姓名為文字輸入框。 | [app.py](file:///C:/Users/awen8/Exam_TutorAI/app.py) |
| **7** | 說明與優化前測 5 題題目重複或記憶問題 | 將診斷前測升級為「動態隨機診斷題庫池」(`DIAGNOSTIC_QUESTION_POOLS`)，每次前測從 5 大核心知識領域隨機抽取 5 題。 | [app.py](file:///C:/Users/awen8/Exam_TutorAI/app.py) |
| **8** | 備份目前的檔案，檔名命名為 11507 版 | 完成備份資料夾 `backup_11507版/` 與壓縮檔 `11507版.zip` (約 4.08 MB)。 | [11507版.zip](file:///C:/Users/awen8/Exam_TutorAI/11507版.zip)<br>[backup_11507版](file:///C:/Users/awen8/Exam_TutorAI/backup_11507版) |
| **9** | 製作開發歷程紀錄檔與今日對話紀錄摘要 | 產生詳細開發歷程檔與本日對話摘要檔。 | [DEVELOPMENT_LOG.md](file:///C:/Users/awen8/Exam_TutorAI/DEVELOPMENT_LOG.md)<br>[CONVERSATION_SUMMARY.md](file:///C:/Users/awen8/Exam_TutorAI/CONVERSATION_SUMMARY.md) |

---

## 🔑 關鍵功能指引與操作

### 1. 學生端使用流程
1. **輸入資料**：選取班級（`801`~`821`）、座號（`01`~`30`）並輸入姓名。
2. **起點前測**：完成 5 題隨機診斷題，系統判定等級（`🌱 Level A` / `🌿 Level B` / `🌳 Level C`）。
3. **適性學習**：
   * `📖 單元重點與講義`：觀看講義全文或點選「🪄 生成專屬 3 分鐘記憶卡」。
   * `✍️ AI 智慧隨堂測驗`：進行 3 題選擇題 + 1 題簡答題適性測驗與 AI 閱卷評語。
   * `🏆 會考段考模擬試題`：抽取歷屆擬真考題練習。
   * `💡 公民 AI 隨問隨答`：輸入問題，由 AI 老師以日常生活與校園實例解惑。

### 2. 教師端管理流程
* 前往 **`Tab 5 👨‍🏫 教師歷程紀錄與後台`**：
  * 檢視全班學生名冊、前測成績、評定等級、測驗次數與最後活動時間。
  * 點擊 **「📥 匯出全班學習歷程 CSV 報表 (Excel 格式)」** 儲存至電腦。
  * 下拉選擇特定學生，調閱其簡答題作答內容、AI 評語與問答紀錄。

---

## 🛠️ 技術檔案架構備忘

* **主程式**：[app.py](file:///C:/Users/awen8/Exam_TutorAI/app.py)
* **講義載入器**：[data_loader.py](file:///C:/Users/awen8/Exam_TutorAI/data_loader.py)
* **日誌紀錄器**：[logger_utils.py](file:///C:/Users/awen8/Exam_TutorAI/logger_utils.py)
* **科目設定檔**：[config.json](file:///C:/Users/awen8/Exam_TutorAI/config.json)
* **試題資料庫**：[question_bank.json](file:///C:/Users/awen8/Exam_TutorAI/question_bank.json)
* **講義檔案目錄**：[materials/](file:///C:/Users/awen8/Exam_TutorAI/materials)
* **學生歷程目錄**：[student_logs/](file:///C:/Users/awen8/Exam_TutorAI/student_logs)
* **11507 版備份檔**：[11507版.zip](file:///C:/Users/awen8/Exam_TutorAI/11507版.zip)
* **完整開發歷程**：[DEVELOPMENT_LOG.md](file:///C:/Users/awen8/Exam_TutorAI/DEVELOPMENT_LOG.md)

# 📑 Exam_TutorAI — 國中八年級公民 AI 智慧學習系統開發歷程紀錄檔

**系統名稱**：Exam_TutorAI 國中八年級公民 AI 智慧學習館  
**版本編號**：`11507版`  
**建立時間**：2026-07-19  
**開發狀態**：已完成轉型、適性前測診斷、高對比前台介面與教師歷程匯出功能  

---

## 📌 一、 專案轉型與核心目標

原本的系統架構為「公務人員高考/地特 社會學 AI 助教」，已全面升級轉型為專為**國中八年級學生設計的「公民類科 AI 智慧學習館」**。

### 核心設計目標：
1. **課程對齊**：全面對齊國中八年級公民領域（國家組成與民主政治、憲法與人民基本權利、法治社會與五院政府運作）。
2. **適性對話**：提供適合 13-14 歲國中生的親切白話解說、動態適性隨堂測驗與 AI 引導式閱卷。
3. **起點前測**：學生登錄班級座號後進行 5 題起點能力前測，平台自動評定等級 (`Level A/B/C`) 並提供專屬學習建議。
4. **歷程追蹤與報表**：採用 JSON 獨立檔案紀錄每位學生的學習點滴，並提供教師後台一鍵匯出 Excel (CSV) 報表。

---

## 🛠️ 二、 詳細開發階段歷程與里程碑

### 🔹 階段 1：教材解析與格式自動轉譯
* **遭遇問題**：原始教材檔為 Word 97-2003 `.doc` 格式 (`08_01_L1.doc` ~ `08_01_L2_tr.doc`)，Streamlit 與 `python-docx` 無法原生讀取。
* **解決技術**：
  * 使用 Python `win32com.client` 開啟 `.doc` 檔並進行控制字元清理與 XML 合規過濾。
  * 成功轉譯為乾淨合規的 `.docx` 格式，存放於 `materials/` 資料夾：
    * `八上第1課：國家與民主政治` (教材與深耕大解析)
    * `八上第2課：憲法與權利保障` (教材與深耕大解析)

### 🔹 階段 2：系統設定與國中公民題庫建置
* **設定檔調整 (`config.json`)**：
  * 主題更新為 `國中八年級公民`，角色更換為 `國中八年級公民科 AI 助教`。
* **資料載入器重構 (`data_loader.py`)**：
  * 增加檔名對映對照表，自動將 `08_01_L1` 轉為繁體中文單元選單。
* **擬真會考題庫建置 (`question_bank.json`)**：
  * 建置國家四大要素、民主政治四原則（民意/法治/責任/政黨）、法律三位階與憲法第23條（比例原則）試題。

### 🔹 階段 3：前台 UI 升級與高對比閱讀器
* **介面視覺優化 (`app.py`)**：
  * 導入 **Glassmorphism 毛玻璃視覺系統**、深靛藍夜空主題與 Hero Banner。
* **高對比閱讀視窗 (`.reader-container`)**：
  * 解決深色模式下講義文字對比度弱的問題，採用純黑藍背景 (`#0f172a`) 與高亮度白字 (`#ffffff`)，配以 1.85 倍行高與紫藍色滾動條。

### 🔹 階段 4：Google Gemini API 模型 404 容錯備援 (Fallback)
* **遭遇問題**：Gemini API 將 `gemini-2.5-flash` 模型退役，導致產生 404 錯誤。
* **解決技術**：
  * 封裝 `call_gemini_api()` 函式，自動在 `gemini-3.5-flash`、`gemini-flash-latest`、`gemini-2.0-flash` 模型間自動備援切換，確保服務不中斷。

### 🔹 階段 5：學生登錄、起點能力前測與適性化學習
* **基本資料登記**：
  * 班級：`801` ~ `821`（下拉式選單）
  * 座號：`01` ~ `30`（下拉式選單）
  * 姓名：手動輸入框
* **動態隨機診斷題庫池 (`DIAGNOSTIC_QUESTION_POOLS`)**：
  * 建立涵蓋 5 大核心知識維度的 15 題題庫池，每次登錄或重測隨機抽取 5 題。
  * 依得分自動評定 `🌱 Level A 基礎`、`🌿 Level B 進階` 或 `🌳 Level C 核心素養專家`，並將等級帶入 AI 提示詞實現適性對話。

### 🔹 階段 6：學習歷程紀錄與教師管理後台 (方案二)
* **日誌紀錄模組 (`logger_utils.py`)**：
  * 於 `student_logs/` 自動建立個別 JSON 檔案（如 `801_12_王大明.json`），記錄前測得分、單元測驗、模擬考與 AI 問答點滴。
* **教師後台 (`Tab 5`)**：
  * 全班學習總覽清單與 **一鍵下載 UTF-8-BOM CSV 報表**（Excel 開啟不亂碼）。
  * 個別學生詳細學習歷程調閱視窗。

### 🔹 階段 7：版本備份 (`11507版`)
* 完成備份資料夾 `backup_11507版/` 與壓縮檔 `11507版.zip` (約 4.08 MB)。

---

## 📂 三、 系統檔案結構總覽

| 檔案/資料夾名稱 | 類型 | 說明 |
| :--- | :--- | :--- |
| [app.py](file:///C:/Users/awen8/Exam_TutorAI/app.py) | Python 主程式 | Streamlit 介面、適性測驗邏輯、學習前測與教師後台 |
| [data_loader.py](file:///C:/Users/awen8/Exam_TutorAI/data_loader.py) | 模組 | 載入與解析 `materials/` 中的 `.docx` 八年級公民講義 |
| [logger_utils.py](file:///C:/Users/awen8/Exam_TutorAI/logger_utils.py) | 模組 | 學生學習歷程 JSON 寫入、讀取與 CSV 報表生成 |
| [config.json](file:///C:/Users/awen8/Exam_TutorAI/config.json) | 設定檔 | 設定國中八年級公民科目名稱與 AI 助教角色 |
| [question_bank.json](file:///C:/Users/awen8/Exam_TutorAI/question_bank.json) | 資料庫 | 國中八年級公民會考/段考擬真題庫 |
| [materials/](file:///C:/Users/awen8/Exam_TutorAI/materials) | 資料夾 | 轉換後之八上公民講義 `.docx` 檔案 |
| [student_logs/](file:///C:/Users/awen8/Exam_TutorAI/student_logs) | 資料夾 | 學生個人學習歷程 JSON 日誌 |
| [11507版.zip](file:///C:/Users/awen8/Exam_TutorAI/11507版.zip) | 備份檔 | 11507 版完整系統備份壓縮檔 |
| [DEVELOPMENT_LOG.md](file:///C:/Users/awen8/Exam_TutorAI/DEVELOPMENT_LOG.md) | 文件 | 本開發歷程紀錄檔 |

---

## 🎯 四、 未來維護與擴充建議
1. **講義續擴**：後續若拿到「八下」或「九年級」講義 `.docx` 檔案，只需直接放進 `materials/` 資料夾，並在 `data_loader.py` 設定對應選單即可自動載入。
2. **題庫擴充**：若要新增題庫，可直接於 `question_bank.json` 中追加題目物件。

# 📑 CivilEdu_AI — 2026-08-30 開發紀錄檔 (Development Log)

**專案名稱**：CivilEdu_AI 國中公民思辨星系 ｜ AI 智慧自主學習館  
**開發日期**：2026-08-30  
**核心主題**：視覺美學全面升級（學測銀河系風格）、全系統流程分析與 Mermaid 設計圖產出、專案名稱一致化 (`CivilEdu_AI`)  

---

## 🎯 一、 今日開發重點總覽 (Key Highlights)

### 1. 🌌 視覺美學全面升級（導入「學測銀河系 GSAT Exam Galaxy」風格）
- **核心理念**：維持既有**所有系統流程、測驗計分、AI 對話、單元管理與資料庫 100% 不變**，僅升級 CSS 樣式與視覺元件結構。
- **墨染深邃水墨夜空**：
  - 捨棄舊版生硬紫色漸層，引入深海墨夜底色（`#060b16` ➜ `#0a1526` ➜ `#0d1c33`）。
  - 疊加直徑數十 rem 的天青藍水墨柔光（Radial Ink Wash）與細微羊皮紙微光質感。
- **雙字體古典排版學 (Typography Hierarchy)**：
  - 大標題、單元名稱與數據指標：全面升級為 **`Noto Serif TC`（思源宋體 / 明體）**，呈現經典書籍與學術星圖的沉穩質感。
  - 眉標（Eyebrow）：引入超寬字距（`letter-spacing: 0.26em`）金色小標（`#95c6f4`）。
  - 內文與選項：維持清晰易讀的 `Noto Sans TC`（思源黑體）。
- **頂部星系導覽與品牌印記**：
  - 學生端：深藍色古典方塊印章 **「民」** + 動態呼吸燈（`● 星軌運行中` 脈衝發光圓點動畫）。
  - 教師端：專屬品牌方印 **「師」** + 「教師星系觀測中心」專業 Header。
- **手札式 01 / 02 序號卡片**：
  - 核心學習重點以大號宋體序號浮水印（`01`, `02`, `03`）卡片呈現，滑鼠懸停時微泛天青光暈。
- **公民星系觀測站 (Civics Observatory)**：
  - 「我的足跡」升級為天文台儀表式大數字橫幅（`🔭 巡航探索單元` ｜ `✨ 已點亮星宿` ｜ `🎯 觀念掌握度`）。
- **極簡星軌 Tab 導覽**：
  - 膠囊狀半透明切換籤，選中時底部呈現天青琥珀金（`#f4d38b`）高亮指示線。

---

### 2. 🛡️ 專案完整安全性備份
- 在進行風格改造與目錄重命名之前，建立雙重完整備份：
  - 📁 **備份資料夾**：`C:\Users\awen8\Exam_TutorAI_backup_20260830`
  - 🗜️ **備份壓縮檔**：`C:\Users\awen8\Exam_TutorAI_backup_20260830.zip`（約 8.6 MB）

---

### 3. 🗺️ 系統分析與 Mermaid 網站流程設計圖
- 針對目前系統進行全面的架構剖析與功能模組梳理。
- 產出結構清晰、相容於 [Mermaid Live Editor](https://mermaid.live/) 與 Mermaid Chart 的**全系統流程設計圖**與**自適應學習閉環狀態圖**。

---

### 4. 📂 本地專案名稱對齊與目錄切換 (`CivilEdu_AI`)
- 解決本地專案資料夾名稱 (`Exam_TutorAI`) 與 GitHub 遠端倉庫 (`https://github.com/SevynLee777/CivilEdu_AI.git`) 命名不一致之問題。
- 完整遷移至 **`C:\Users\awen8\CivilEdu_AI`**，包含完整的 Git 歷史、單元資料庫與學習紀錄。
- 修訂 `run.bat`、`README.md` 中的專案名稱與說明。
- 順利將工作環境切換至新目錄 `C:\Users\awen8\CivilEdu_AI`。

---

## 🛠️ 二、 詳細修訂檔案與模組對照

| 檔案名稱 | 類型 | 本次修訂重點說明 |
| :--- | :--- | :--- |
| [`app.py`](file:///C:/Users/awen8/CivilEdu_AI/app.py) | 主程式 | 注入「學測銀河系」CSS 樣式表（思源宋體、水墨光暈、金色眉標、呼吸燈狀態列、01/02 序號卡片、觀測站橫幅）。 |
| [`README.md`](file:///C:/Users/awen8/CivilEdu_AI/README.md) | 專案說明 | 更新專案標題為 `🏛️ CivilEdu_AI (國中公民 AI 智慧自主學習館 / 公民思辨星系)`。 |
| [`run.bat`](file:///C:/Users/awen8/CivilEdu_AI/run.bat) | 啟動腳本 | 更新輸出文字為 `Starting CivilEdu_AI...`。 |
| [`DEVELOPMENT_LOG_20260830.md`](file:///C:/Users/awen8/CivilEdu_AI/DEVELOPMENT_LOG_20260830.md) | 開發紀錄 | 本日開發歷程與系統更新紀錄檔（新增）。 |
| [`DEVELOPMENT_LOG.md`](file:///C:/Users/awen8/CivilEdu_AI/DEVELOPMENT_LOG.md) | 主紀錄文件 | 補充「階段 10：視覺星系美學升級與專案目錄一致化」。 |

---

## 🚀 三、 啟動與操作指令

在 **PowerShell** 環境下，直接在最新專案目錄啟動服務：

```powershell
# 1. 切換至專案目錄
Set-Location "C:\Users\awen8\CivilEdu_AI"

# 2. 啟動 Streamlit 服務
python -m streamlit run app.py
```
*(或在檔案總管雙擊執行 `C:\Users\awen8\CivilEdu_AI\run.bat`)*

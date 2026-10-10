# 📑 CivilEdu_AI — 2026-10-10 本日完整開發紀錄檔 (Development Log)

**專案名稱**：CivilEdu_AI 國中公民思辨星系 ｜ AI 智慧自主學習館  
**開發日期**：2026-10-10  
**核心主題**：教師端教材檔案直接上傳解析（含舊版 Word .doc 與 .docx/.pdf/.txt/.md）、小試身手隨機選題/題序/選項洗牌演算法、各單元生活案例擴充至 4 則、Streamlit Cloud 熱重載與解析容錯安全防護  
**版本標籤**：`2026-10-10-v2`  

---

## 🎯 一、 今日開發里程碑總覽 (Milestones Summary)

今日（2026-10-10）針對使用者提出之核心需求與雲端部署實務進行全面升級：

| 需求序號 | 主題 | 影響模組 | 核心成果摘要 |
| :---: | :--- | :--- | :--- |
| **一** | **教材檔案直接上傳（全面支援 .doc / .docx / .pdf / .txt / .md）** | [`app.py`](file:///C:/Users/awen8/CivilEdu_AI/app.py)<br>[`unit_manager.py`](file:///C:/Users/awen8/CivilEdu_AI/unit_manager.py)<br>[`requirements.txt`](file:///C:/Users/awen8/CivilEdu_AI/requirements.txt) | 支援直接上傳新舊版 Word（`.docx` 與舊版 Word 97-2003 `.doc`）、`.pdf`、`.txt`、`.md` 文件，自動解析段落、計算字數並自動填入單元名稱與內容；支援直接一鍵 AI 生成或手動編輯微調，修改教材亦同步支援檔案替換。採用純 Python OLE2 串流解析，完全支援 Linux/Streamlit Cloud。 |
| **二** | **隨機選題、題序與選項洗牌** | [`app.py`](file:///C:/Users/awen8/CivilEdu_AI/app.py)<br>[`unit_manager.py`](file:///C:/Users/awen8/CivilEdu_AI/unit_manager.py)<br>[`units_db.json`](file:///C:/Users/awen8/CivilEdu_AI/units_db.json) | 各單元題庫池擴充至 16 道素養選擇題，每次測驗動態隨機抽取 8 題、題序隨機打散、每題 ABCD 選項隨機洗牌，且正確答案動態精準對齊；重新測驗時自動刷新為全新題組。 |
| **三** | **各單元生活案例增加為 4 則** | [`units_db.json`](file:///C:/Users/awen8/CivilEdu_AI/units_db.json)<br>[`unit_manager.py`](file:///C:/Users/awen8/CivilEdu_AI/unit_manager.py)<br>[`app.py`](file:///C:/Users/awen8/CivilEdu_AI/app.py) | 第一課與第二課生活案例由 2 則全面擴增為 4 則完整實例（涵蓋校園自治、日常生活、網路社群、社區公共），每則均包含故事描述與思辨焦點；AI 單元生成提示詞同步升級。 |
| **四** | **Streamlit Cloud 熱重載與例外安全包裝** | [`app.py`](file:///C:/Users/awen8/CivilEdu_AI/app.py) | 針對雲端容器（Streamlit Cloud）模組快取熱重載可能產生之 `AttributeError`，建立安全自動 reload 與 `safe_extract_text_from_file_upload` / `safe_randomize_practice_questions` 本地雙重保險降級防護。 |

---

## 📂 二、 需求一：教師端「教材單元管理」直接上傳檔案

#### 1. 需求分析與操作痛點
原先系統僅提供空白文字輸入框要求教師手動複製貼上，若講義排版繁複或為 PDF/Word 文件，複製過程易遺漏格式或產生換行錯置。特別是國中許多資深教師留存的珍貴講義仍為舊版 Word 97-2003（`.doc`）格式，需要能原生支援直接上傳與自動解碼。

### 2. 架構設計與 Mermaid 流程圖

```mermaid
flowchart TD
    A["教師選取或拖曳檔案 (.doc, .docx, .pdf, .txt, .md)"] --> B["extract_text_from_file_upload() 檔案萃取引擎"]
    B --> C1{"檔案格式判斷"}
    C1 -->|舊版 Word .doc| D0["olefile + MS-DOC FIB/Clx Piece Table 純 Python 解析"]
    C1 -->|Word .docx| D1["python-docx 提取段落與文字結構"]
    C1 -->|PDF .pdf| D2["pdfplumber 逐頁萃取文字內容"]
    C1 -->|Text / MD| D3["UTF-8 / CP950 容錯編碼解碼"]
    D0 --> E["自動提取檔名作為單元名稱建議"]
    D1 --> E
    D2 --> E
    D3 --> E
    E --> F["自動帶入下方表單預覽（單元名稱 ＆ 教材內容）"]
    F --> G["教師可直接送出或進一步編輯補充"]
    G --> H["AI 智慧分析：萃取重點、4 則生活案例、心智圖、16 題題庫池與補救指南"]
```

### 3. 技術實作亮點
1. **舊版 Word 97-2003 (`.doc`) 純 Python OLE2 串流解析 ([`unit_manager.py`](file:///C:/Users/awen8/CivilEdu_AI/unit_manager.py#L90-L175))**：
   - **雲端相容性突破**：Streamlit Cloud 為 Linux 容器環境，無法依賴 Windows 獨有的 `win32com`，亦不宜依賴繁雜的系統二進位外掛套件。
   - **實作 `extract_text_from_doc_bytes()`**：
     - 利用純 Python 套件 `olefile` 讀取 OLE2/CFBF 複合二進位串流。
     - 解析 `WordDocument` 串流頂部之 FIB (File Information Block)，判定 Table 串流名稱（`0Table` 或 `1Table`）。
     - 讀取 FIB 偏移量 `0x01A2` 之 `fcClx` 與 `lcbClx`，精確鎖定 Complex File Structure (Clx)。
     - 遍歷 Clx 內的 Piece Table (`Plcfpcd`)，解析每個 Piece 的字元計數與二進位偏移位置 (`fc`)。
     - 區分壓縮字元（8-bit ANSI/CP950）與標準雙字節 Unicode（UTF-16LE），精準還原長篇講義文字與標點符號，完整相容如 `08_01_L1.doc`（4,549 字）等各類學校講義。
2. **多格式文件文字萃取引擎 ([`unit_manager.py`](file:///C:/Users/awen8/CivilEdu_AI/unit_manager.py))**：
   - 封裝 [`extract_text_from_file_upload(file_input, filename)`](file:///C:/Users/awen8/CivilEdu_AI/unit_manager.py)，同時相容記憶體 Bytes 與 Streamlit 的 `UploadedFile`。
   - 自動在讀取前、後執行 `seek(0)` 重置檔案指標，防止連續讀取時游標觸底。
   - 自動自檔案名稱剝除副檔名作為單元名稱預設值。
   - 編碼容錯：針對文字檔優先以 `utf-8` 解碼，失敗時自動以 `cp950` 回退，徹底杜絕 Windows 常見之 `UnicodeDecodeError`。
3. **表單狀態雙向綁定 ([`app.py`](file:///C:/Users/awen8/CivilEdu_AI/app.py#L1265-L1350))**：
   - 透過檔案特徵簽章 (`file_sig = f"{uploaded_file.name}_{uploaded_file.size}"`) 偵測檔案變動，避免 Streamlit 每次 rerun 時重複解析。
   - 顯示醒目的成功提示標籤（如：`✅ 已成功從檔案【xxx.doc】讀取 4,549 字！`）。
   - 修改現有教材單元時，亦提供專屬檔案上傳器，便利教師隨時替換內容並選擇是否重新由 AI 生成重點。

---

## 🎲 三、 需求二：「小試身手」隨機選題、題序與選項隨機排列

### 1. 核心問題與解決方針
原系統中各單元僅有固定的 8 題，且題序與選項固定，導致學生二次複習時題目完全相同且容易記憶選項位置（如「第 1 題選 A、第 2 題選 B」）。

### 2. 隨機洗牌演算法設計 ([`unit_manager.py`](file:///C:/Users/awen8/CivilEdu_AI/unit_manager.py#L137-L175))

```mermaid
flowchart TD
    Pool["單元題庫池 (16 題高質量情境素養題)"] --> Step1["1. 隨機選題：random.sample(pool, 8)"]
    Step1 --> Step2["2. 隨機排題序：random.shuffle(selected_questions)"]
    Step2 --> Step3["3. 逐題遍歷與深拷貝 (deepcopy)"]
    Step3 --> Step4["剝除既有 A/B/C/D 前綴並記錄正解文字"]
    Step4 --> Step5["4. 隨機排選項：random.shuffle(clean_options)"]
    Step5 --> Step6["重新標記 A) B) C) D) 前綴"]
    Step6 --> Step7["計算正解在打亂後清單之新索引：new_correct_index"]
    Step7 --> State["存入 Session State (active_practice_qs) 綁定輪次 ID"]
```

### 3. 技術實作重點
1. **題庫池擴充至 16 題 ([`units_db.json`](file:///C:/Users/awen8/CivilEdu_AI/units_db.json))**：
   - 為「第 1 課：國家與民主政治」補充 `q9` ~ `q16`（人民要素、國籍認定、依法行政、政黨政治良性競爭、代議民主與公投、國家主權特徵、公務員責任類型、多數決與少數尊重）。
   - 為「第 2 課：憲法與權利保障」補充 `q9` ~ `q16`（秘密通訊與隱私權、生存權與給付受益權、罷免權、比例原則三大子原則、法律保留原則、實質平等與弱勢優惠、違憲審查制度、集會遊行自由）。
2. **選項文字剝除與動態對位**：
   - 使用正規表達式 `re.sub(r'^[A-Da-d]\s*[\)\.\、\:\-]?\s*', '', str(opt)).strip()` 清除原本前綴。
   - 記錄正確選項字串 `correct_content = clean_options[orig_corr_idx]`。
   - 隨機洗牌選項後使用 `clean_options.index(correct_content)` 重新鎖定 `correct_index`，保證 100% 正確率。
3. **Session State 生命週期管理**：
   - 將抽取後的題目託管於 `st.session_state[f"active_practice_qs_{unit_id}"]`，避免使用者在勾選單選題畫面 rerun 時題目突然變更。
   - 納入輪次編號 `practice_round_{unit_id}`，radio widget key 設定為 `p_q_{unit_id}_{current_round}_{i}`，重測時整組 widget 徹底重置，不殘留上一輪選中狀態。
   - 點擊「🔄 重新小試身手（隨機新題目與新選項）」時，立即推進輪次編號並產生新題組。

---

## 🏫 四、 需求三：各學習單元生活案例擴充為 4 則

### 1. 各課次 4 則生活情境案例總表

#### 📖 第 1 課：國家與民主政治
| 案例序號 | 情境主題 | 案例故事摘要 | 思辨焦點 |
| :---: | :--- | :--- | :--- |
| **案例 1** | 🏫 校園生活：班會選幹部與制定班規 | 每學期初透過不記名投票選出班長與表決班規，失職可依程序改選。 | 💡 「民意政治」與「責任政治」在班級生活的具體縮影！ |
| **案例 2** | 🏪 日常生活：出國護照與主權象徵 | 國民持中華民國護照出國旅遊通關，代表國家主權的法律保護。 | 💡 主權對外獨立，賦予國民在國際上的明確地位與保障！ |
| **案例 3** | 📱 網路社群：學生會粉專留言與網路公民權 | 學生在粉專提出手機使用規範建言，引發討論並促成行政主管座談會。 | 💡 透過理性多元管道參與公共事務，是「民意政治」的蓬勃實踐！ |
| **案例 4** | 🚌 社區生活：里民大會參與與公共設施公聽會 | 里民大會討論公園遊樂設施與人行道拓寬，投票後里長向公所反映爭取。 | 💡 地方自治與基層參與，讓民主落實在日常周遭生活！ |

#### 📖 第 2 課：憲法與權利保障
| 案例序號 | 情境主題 | 案例故事摘要 | 思辨焦點 |
| :---: | :--- | :--- | :--- |
| **案例 1** | 🏫 校園生活：校規若牴觸法律誰有效？ | 教育部規定不得因服儀懲處學生，學校校規若與上位規範牴觸則無效。 | 💡 下位階規範不得牴觸上位階規範，保障學生基本權益！ |
| **案例 2** | 🏪 日常生活：颱風天停班停課與基本權限制 | 颱風來襲時依法管制登山，為了「避免緊急危難」依法做出正當限制。 | 💡 自由不是無限大，政府限制自由必須依法且符合比例原則！ |
| **案例 3** | 🚶 街頭情境：警察臨檢盤查與人身自由保障 | 警察臨檢盤查依法出示證件並說明事由，不可無故任意搜身或扣留物品。 | 💡 人身自由是各項自由的基石，公權力行使須符合正當法律程序！ |
| **案例 4** | 🛒 消費生活：消保爭議與定型化契約無效 | 網購業者訂立「售出概不退貨」條款，消保官指牴觸消保法宣告該條款無效。 | 💡 私人契約約定不得牴觸國家法律，法律保障弱勢消費者權益！ |

### 2. AI 自動生成提示詞全面同步
在 [`unit_manager.py`](file:///C:/Users/awen8/CivilEdu_AI/unit_manager.py) 中更新提示詞規範：
- 明確要求輸出滿 4 個情境實例（包含校園生活、日常生活、網路社群、社區公共生活）。
- 出滿 16 道生活情境單選題（`q1` 至 `q16`），以支撐後續隨機選題。
- 備援生成器 [`get_default_fallback_bundle()`](file:///C:/Users/awen8/CivilEdu_AI/unit_manager.py#L225) 同步配置 4 個生活案例與 16 道題目。

---

## 🛡️ 五、 雲端部署防護：Streamlit Cloud 熱重載與模組快取安全機制

### 1. 遭遇問題 (AttributeError)
在 Streamlit Cloud 容器熱部署時，若模組檔案已更新但 Streamlit 行程尚未重啟，Python 之 `sys.modules` 可能殘留舊版 `unit_manager` 快取，導致呼叫 `unit_manager.extract_text_from_file_upload` 時拋出：
```
AttributeError: module 'unit_manager' has no attribute 'extract_text_from_file_upload'
```

### 2. 雙重安全防護機制 ([`app.py`](file:///C:/Users/awen8/CivilEdu_AI/app.py))
1. **模組強制刷新機制**：在 `app.py` 頂部引用 `import importlib`，自動執行 `importlib.reload(unit_manager)`，確保每次雲端重新載入時均取得最新程式碼物件。
2. **本地備援包裝器 (`safe_extract_text_from_file_upload`)**：
   - 優先呼叫 `unit_manager.extract_text_from_file_upload`。
   - 若發生 `AttributeError` 或函式尚未註冊，自動切換至 `app.py` 內建的本機萃取備援邏輯（含 `.doc`, `.docx`, `.pdf`, `.txt` 解碼），徹底消除應用程式崩潰風險。
3. **測驗洗牌備援包裝器 (`safe_randomize_practice_questions`)**：
   - 同步加入備援呼叫，若模組未及時更新亦可在本地完成隨機抽題與選項打散。

---

## 🧪 六、 整合測試與驗證紀錄

透過自動化腳本驗證三大需求與 `.doc` 支援之核心邏輯：

```
=== 測試 1: 檔案解析功能 (含新舊版 Word、PDF、文字檔) ===
Docx - 建議名稱: 第3課_政府的組織
Docx - 解析字數: 19 內文預覽: 這是第一段教材內容 這是第二段重點概念
Txt  - 建議名稱: 公民重點講義
Txt  - 解析字數: 18
Doc  - 檔案: 08_01_L1.doc (Word 97-2003 OLE2) -> 解析字數: 4,549 字
Doc  - 檔案: 08_01_L2.doc (Word 97-2003 OLE2) -> 解析字數: 4,818 字
首行驗證: "第四篇　民主政治的運作"、"憲法是國家的根本大法，是人民權利的保障書..." 繁體中文全數精準還原！

=== 測試 2: 小試身手隨機選題、題序與選項洗牌 ===
單元: 第1課：國家與民主政治, 題庫池總題數: 16
-- 第 1 輪隨機抽出題數: 8 --
抽中題目ID與題序: ['q12', 'q3', 'q4', 'q8', 'q7', 'q9', 'q10', 'q2']
第1題 [主權在民]: 正確選項 -> C) 公民投票（公投）對重大公共政策或法律原則行使複決或創制
-- 第 2 輪隨機抽出題數: 8 --
抽中題目ID與題序: ['q11', 'q1', 'q10', 'q13', 'q3', 'q12', 'q7', 'q8']
第1題 [政黨政治]: 正確選項 -> C) 各政黨提出政策主張爭取選民認同，在野黨監督施政並循和平選舉爭取執政
-- 第 3 輪隨機抽出題數: 8 --
抽中題目ID與題序: ['q10', 'q5', 'q12', 'q4', 'q6', 'q8', 'q11', 'q1']
第1題 [法治政治]: 正確選項 -> B) 防止政府公權力濫用，以切實保障人民的基本權利

=== 測試 3: 生活案例數量檢查 ===
單元【第1課：國家與民主政治】生活案例數量: 4 個
  案例 1: 🏫 校園生活：班會選幹部與制定班規
  案例 2: 🏪 日常生活：出國護照與主權象徵
  案例 3: 📱 網路社群：學生會粉專留言與網路公民權
  案例 4: 🚌 社區生活：里民大會參與與公共設施公聽會
單元【第2課：憲法與權利保障】生活案例數量: 4 個
  案例 1: 🏫 校園生活：校規若牴觸法律誰有效？
  案例 2: 🏪 日常生活：颱風天停班停課與基本權限制
  案例 3: 🚶 街頭情境：警察臨檢盤查與人身自由保障
  案例 4: 🛒 消費生活：消保爭議與定型化契約無效

🎉 所有測試通過，邏輯完全正確！
```

---

## 🚀 七、 程式庫版本控制與部署狀態

- **遠端儲存庫**：`https://github.com/SevynLee777/CivilEdu_AI.git`
- **當前分支**：`main`
- **最新提交**：支援舊版 Word 97-2003 (`.doc`) 檔案上傳與 Streamlit Cloud 熱重載雙重安全機制
- **工作區狀態**：已同步推送至 GitHub，Streamlit Cloud 自動觸發持續部署 (CI/CD)


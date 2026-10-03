# 📑 CivilEdu_AI — 2026-09-30 開發紀錄檔 (Development Log)

**專案名稱**：CivilEdu_AI 國中公民思辨星系 ｜ AI 智慧自主學習館  
**開發日期**：2026-09-30  
**核心主題**：Windows 11 Smart App Control (SAC) 應用程式控制原則衝突排查與 Pandas / PyArrow 動態連結庫 (DLL) 載入防禦性修復

---

## 🎯 一、 今日開發與問題修復總覽 (Key Highlights)

### 1. ⚠️ 異常問題發生與現象
- **錯誤訊息**：
  ```text
  ImportError: DLL load failed while importing _compute: An Application Control policy has blocked this file.
  ```
- **衝擊層面**：使用者透過 [`run.bat`](file:///C:/Users/awen8/CivilEdu_AI/run.bat) 或 [`force_launch.py`](file:///C:/Users/awen8/CivilEdu_AI/force_launch.py) 啟動專案時，在 [`app.py`](file:///C:/Users/awen8/CivilEdu_AI/app.py) 引用歷程紀錄模組 [`logger_utils.py`](file:///C:/Users/awen8/CivilEdu_AI/logger_utils.py)（內部引用 `pandas`）階段直接拋出例外中斷，Streamlit 服務完全無法正常開啟。

---

### 2. 🔍 底層根因深度診斷 (Root Cause Analysis)

#### ① Windows 11 Smart App Control (SAC) 安全原則攔截
- 查詢 Windows 事件檢視器記錄（`Microsoft-Windows-CodeIntegrity/Operational`），發現於程序執行時觸發事件：
  - **Event ID 3033 / 3077**：`Code Integrity determined that a process (python.exe) attempted to load ...\_compute.cp311-win_amd64.pyd that did not meet the Enterprise signing level requirements or violated code integrity policy.`
  - **Event ID 3118**：`Smart App Control Block Deteails`。
- 檢驗系統登錄檔 `HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy` 中的 `VerifiedAndReputablePolicyState` 值為 `1`（代表 Smart App Control 處於強制啟用保護狀態）。
- 在該模式下，Windows 核心會對所有二進位執行檔（`.exe`、`.dll`、`.pyd`）進行雲端信譽（Microsoft Intelligent Security Graph, ISG）及 Authenticode 數位簽章檢驗。若檔案缺乏信任簽章且信譽尚未建立，即時回傳 `WinError 4551 (ERROR_STATUS_CONTROL_UNSUCCESSFUL)`。

#### ② PyArrow 二進位模組信譽缺失
- 經由 Python 批次載入測試 `pyarrow 25.0.0` 中的所有 `.pyd` 擴展模組，發現絕大多數模組（如 `lib.pyd`、`_acero.pyd` 等）可正常加載，但以下三個模組遭到 SAC 攔截：
  1. `_compute.cp311-win_amd64.pyd`（WinError 4551）
  2. `_dataset.cp311-win_amd64.pyd`（WinError 4551）
  3. `_parquet_encryption.cp311-win_amd64.pyd`（WinError 4551）

#### ③ Pandas 相容性檢測缺陷
- 在 `pandas 3.0.3` 的 [`pandas/compat/pyarrow.py`](file:///C:/Users/awen8/AppData/Local/Programs/Python/Python311/Lib/site-packages/pandas/compat/pyarrow.py) 中，原設計僅以 `try: import pyarrow as pa` 作為是否具備 PyArrow 支援的判斷依據（此步驟載入 `lib.pyd`，因而通過檢測並將 `HAS_PYARROW` 標記為 `True`）。
- 隨後在 [`pandas/core/arrays/arrow/accessors.py`](file:///C:/Users/awen8/AppData/Local/Programs/Python/Python311/Lib/site-packages/pandas/core/arrays/arrow/accessors.py) 初始化時無條件執行：
  ```python
  if HAS_PYARROW:
      import pyarrow as pa
      import pyarrow.compute as pc  # 此處觸發 _compute 載入失敗崩潰
  ```
- 由於缺乏二級例外防護，導致未捕捉的 `ImportError` 向外蔓延，使 `import pandas` 瞬間終止。

---

### 3. 🛠️ 解決方案與防禦性修復 (Implementation & Fix)

#### ① Pandas 相容層相容性強化
- 編輯 Python 環境中的 [`pandas/compat/pyarrow.py`](file:///C:/Users/awen8/AppData/Local/Programs/Python/Python311/Lib/site-packages/pandas/compat/pyarrow.py)，將 `pyarrow.compute` 提前置入能力偵測區塊：
  ```python
  PYARROW_MIN_VERSION = "13.0.0"
  try:
      import pyarrow as pa
      import pyarrow.compute as pc  # 強化：在能力判定前預先驗證 compute 擴展可用性
      
      _palv = Version(Version(pa.__version__).base_version)
      ...
      PYARROW_INSTALLED = True
      HAS_PYARROW = _palv >= Version(PYARROW_MIN_VERSION)
  except ImportError:
      ...
      PYARROW_INSTALLED = False
      HAS_PYARROW = False
  ```
- **效果**：當 Windows 安全策略封鎖 `_compute` 時，`pandas` 能及時捕獲 `ImportError`，自動將 `HAS_PYARROW` 設為 `False`，平順降級採用原生/NumPy 運算引擎，不再引發系統中斷。

#### ② Streamlit 服務與 Arrow 功能確認
- 經由原始碼篩選確認，Streamlit 本身並未直接引用 `pyarrow.compute`，僅使用 `pyarrow` 基礎資料型別序列化功能，因此在 Pandas 降級後，Streamlit 完全不受影響，運作依然流暢。

---

### 4. 🧪 驗證與測試成果 (Verification)

1. **Pandas 載入驗證**：
   ```powershell
   python -c "import pandas as pd; print('Pandas loaded:', pd.__version__)"
   # 輸出：Pandas loaded: 3.0.3（耗時 < 1 秒，無任何警告與錯誤）
   ```
2. **主應用載入驗證**：
   ```powershell
   python -c "import app; print('App loaded successfully!')"
   # 輸出：App loaded successfully!（單元管理、題庫、紀錄模組均順暢載入）
   ```
3. **Streamlit 伺服器啟動測試**：
   ```powershell
   python -m streamlit run app.py --server.headless=true
   # 輸出：Uvicorn server started on :::8501，Local URL: http://localhost:8501
   ```
   已確認本機與內網連線皆能正常進入國中公民思辨星系首頁。

---

## 🛠️ 二、 詳細修訂檔案對照表

| 檔案名稱 / 路徑 | 類型 | 本次修訂重點說明 |
| :--- | :--- | :--- |
| [`pandas/compat/pyarrow.py`](file:///C:/Users/awen8/AppData/Local/Programs/Python/Python311/Lib/site-packages/pandas/compat/pyarrow.py) | Python 套件環境相容層 | 強化 `HAS_PYARROW` 檢測邏輯，加入 `import pyarrow.compute as pc` 例外捕捉，確保在 Windows SAC 或應用程式控制原則環境下安全降級。 |
| [`DEVELOPMENT_LOG_20260930.md`](file:///C:/Users/awen8/CivilEdu_AI/DEVELOPMENT_LOG_20260930.md) | 開發紀錄 | 本日問題診斷、SAC 根因分析、修復步驟與驗證成果紀錄檔（新增）。 |
| [`DEVELOPMENT_LOG.md`](file:///C:/Users/awen8/CivilEdu_AI/DEVELOPMENT_LOG.md) | 主紀錄文件 | 補充「階段 13：Windows 應用控制原則衝突排查與 Pandas / PyArrow 載入防禦修復」。 |

---

## 💡 三、 相關環境備忘與系統層級建議

若未來在新增其他含有 C/C++ 編譯擴展之套件（例如部分視覺運算或原生加速函式庫）時再次遇到 `An Application Control policy has blocked this file`，可依需求採取以下措施：

1. **檢查 Windows 事件檢視器**：
   - 路徑：`應用程式及服務記錄檔` > `Microsoft` > `Windows` > `CodeIntegrity` > `Operational`。
   - 篩選 Event ID 3033 / 3077，確認遭封鎖的具體二進位檔案路徑。
2. **調整 Smart App Control 狀態（如需要）**：
   - 開啟 **Windows 安全性** > **應用程式與瀏覽器控制** > **智慧型應用程式控制設定**。
   - 考量開發環境經常執行非商業簽章工具，可評估切換為 **評估模式 (Evaluation)** 或 **關閉 (Off)**。

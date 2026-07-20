# 網站健康檢查工具

本專案使用 Playwright 自動開啟網頁，檢查 HTTP 狀態、頁面標題、主標題，並自動截圖。提供**命令列（CLI）**與**圖形介面（GUI）**兩種操作方式。

## 專案結構

```
lesson10/
├── practice5.py          # 核心函式（check_website）與 CLI 入口
├── gui.py                # tkinter GUI 應用程式入口
├── test_practice5.py     # 單元測試
├── requirements.txt      # Python 相依套件
├── output/               # 截圖輸出目錄（自動建立）
└── README.md
```

## 安裝與執行

### 使用 uv（建議）

```bash
# 安裝相依套件
uv pip install -r lesson10/requirements.txt

# 安裝 Playwright 瀏覽器二進位檔
playwright install

# 命令列模式（預設 chromium，無頭模式）
uv run python lesson10/practice5.py

# 指定瀏覽器
uv run python lesson10/practice5.py --browser firefox

# 顯示瀏覽器視窗
uv run python lesson10/practice5.py --no-headless

# 啟動圖形介面
uv run python lesson10/gui.py
```

### 使用 pip

```bash
pip install -r lesson10/requirements.txt
playwright install
python lesson10/practice5.py
python lesson10/gui.py
```

## 執行測試

```bash
uv run pytest lesson10/test_practice5.py -v
```

## 功能說明

- **check_website()**：核心函式，使用 Playwright 開啟網頁、取得 HTTP 狀態碼、頁面標題、主標題、回應時間，並儲存全頁截圖。
- **WebsiteCheckResult**：資料類別，封裝所有檢查結果。
- **GUI 模式**：tkinter 雙欄介面，支援 URL 驗證、瀏覽器選擇、headless 開關、timeout 設定、截圖預覽與執行日誌。
- **背景執行緒**：Playwright 操作在背景執行緒執行，不卡住 GUI。

## 清除輸出

刪除 `output/` 目錄即可清除所有截圖與暫存檔案。
